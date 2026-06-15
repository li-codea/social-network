# 服务层：好友推荐引擎

> **源码文件**：`backend/app/services/recommendation_service.py`

---

## 文件职责

实现好友推荐引擎的核心算法，综合运用三种高级 SQL 技术（CTE 递归查询、JSON_OVERLAPS、共同好友计数）发现潜在好友并按加权评分排序。

**评分公式**：

```
score = common_friends_count × 3
      + common_tags_count × 2
      + (max_degree − degree + 1) × 1
```

---

## 导入依赖

```python
from collections import defaultdict
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.friendship import Friendship
from app.utils.pagination import get_pagination_slice
```

---

## 主函数详解

### `get_recommendations(db, user_id, page, page_size, max_degree)` — 推荐入口

```python
def get_recommendations(
    db: Session, user_id: int,
    page: int = 1, page_size: int = 20, max_degree: int = 3,
) -> tuple[list[dict], int]:
```

**推荐流程**（7 步流水线）：

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CTE 递归查询 → 二度/三度好友                             │
│ 2. JSON_OVERLAPS → 兴趣标签匹配用户                          │
│ 3. 合并候选集 → 按 ID 去重                                  │
│ 4. 批量计算共同好友数                                        │
│ 5. 加权评分排序                                              │
│ 6. 分页截取                                                  │
│ 7. 加载用户详情 + 共同好友详情 → 组装返回                     │
└─────────────────────────────────────────────────────────────┘
```

#### 步骤 3：合并候选集

```python
all_candidates = {}
for cand in cte_candidates:
    all_candidates[cand["id"]] = cand
for cand in tag_candidates:
    if cand["id"] not in all_candidates:
        cand["degree"] = None  # 纯标签匹配，无图谱关系
        all_candidates[cand["id"]] = cand
    else:
        # 已在 CTE 结果中，补充标签匹配信息
        all_candidates[cand["id"]]["common_tags_count"] = cand.get("common_tags_count", 0)
```

| 来源 | degree | 说明 |
|------|--------|------|
| CTE | 2~3 | 图谱中的最短路径距离 |
| 标签 | `None`（后续替换为 `max_degree + 1`） | 仅通过兴趣匹配，无直接社交联系 |

#### 步骤 5：加权评分

```python
score = (
    common_friends_count * 3      # 共同好友：权重最高
    + common_tags_count * 2       # 共同兴趣：权重居中
    + (max_degree - degree + 1) * 1  # 社交距离：权重最低
)
```

| 维度 | 权重 | 含义 |
|------|------|------|
| 共同好友数 | ×3 | 朋友的朋友更可能成为朋友（社交传递性） |
| 共同标签数 | ×2 | 兴趣相投可能成为朋友 |
| 社交距离 | ×1 | 二度好友比三度好友更近 |

**排序**：先按评分降序（`-x["score"]`），评分相同按度数升序（更近的排前面）。

---

## 辅助函数详解

### `_get_cte_candidates(db, user_id, max_degree)` — CTE 递归查询

```python
def _get_cte_candidates(db: Session, user_id: int, max_degree: int) -> list[dict]:
```

使用 MySQL `WITH RECURSIVE` 从句实现图遍历：

```sql
WITH RECURSIVE friend_graph AS (
    -- BASE CASE: 目标用户的一度好友
    SELECT
        CASE WHEN user_id = :uid THEN friend_id ELSE user_id END AS connected_id,
        1 AS degree
    FROM friendships
    WHERE user_id = :uid OR friend_id = :uid

    UNION ALL

    -- RECURSIVE STEP: 向外扩展一跳
    SELECT
        CASE WHEN f.user_id = fg.connected_id THEN f.friend_id ELSE f.user_id END,
        fg.degree + 1 AS degree
    FROM friendships f
    INNER JOIN friend_graph fg
        ON (f.user_id = fg.connected_id OR f.friend_id = fg.connected_id)
    WHERE fg.degree < :max_deg
)
SELECT DISTINCT connected_id AS id, MIN(degree) AS shortest_degree
FROM friend_graph fg
WHERE fg.connected_id != :uid
  AND fg.connected_id NOT IN (
      -- 排除已是一度好友
      SELECT CASE WHEN user_id = :uid THEN friend_id ELSE user_id END
      FROM friendships WHERE user_id = :uid OR friend_id = :uid
  )
  AND fg.degree BETWEEN 2 AND :max_deg
GROUP BY fg.connected_id
ORDER BY shortest_degree ASC
```

| SQL 部分 | 说明 |
|----------|------|
| **BASE CASE** | 从目标用户出发，找到所有一度好友 |
| **RECURSIVE STEP** | 从当前节点沿无向边继续向外扩展，degree + 1 |
| `fg.degree < :max_deg` | 递归终止条件：达到最大度数时停止 |
| `DISTINCT + MIN(degree)` | 如果有多个路径到达同一用户，取最短路径 |
| `NOT IN` 子查询 | 排除已经是一度好友的用户 |
| `degree BETWEEN 2 AND :max_deg` | 只保留二度及以上（一度好友不需要推荐） |

**图遍历示意**（`max_degree=3`）：

```
目标用户 Alice
    │ 一度好友
    ├── Bob ───── 二度好友
    │   └── Eve      ↑
    ├── Carol        推荐给 Alice
    │   └── Eve
    └── Dave
```

Eve 通过两条路径到达（degree=2 via Bob, degree=2 via Carol），`MIN(degree)` 取 2。

### `_get_tag_candidates(db, user_id, target_tags)` — 标签匹配

```python
def _get_tag_candidates(db: Session, user_id: int, target_tags: list[str]) -> list[dict]:
```

使用 MySQL 8.0 的 `JSON_OVERLAPS` 函数：

```sql
SELECT u.id, u.nickname, u.avatar_url, u.tags
FROM users u
WHERE u.id != :uid
  AND u.tags IS NOT NULL
  AND JSON_OVERLAPS(u.tags, CAST(:target_tags AS JSON)) = 1
  AND u.id NOT IN (
      -- 排除已是一度好友
      SELECT CASE WHEN user_id = :uid THEN friend_id ELSE user_id END
      FROM friendships WHERE user_id = :uid OR friend_id = :uid
  )
LIMIT 100
```

| 技术要点 | 说明 |
|----------|------|
| `JSON_OVERLAPS(a, b)` | 返回 1 当两个 JSON 数组有至少一个公共元素 |
| `CAST(:target_tags AS JSON)` | 将传入的 JSON 字符串参数转为 MySQL JSON 类型 |
| `LIMIT 100` | 限制标签匹配的候选数量，避免候选集过大 |
| Python 计算具体重叠数 | SQL 只负责找到有交集的用户，具体重叠标签数在 Python 中用 `set & set` 计算 |

### `_batch_common_friends_count(db, user_id, candidate_ids)` — 批量共同好友计数

```python
def _batch_common_friends_count(
    db: Session, user_id: int, candidate_ids: list[int]
) -> dict[int, int]:
```

**设计目标**：一次 SQL 查询完成目标用户与所有候选用户的共同好友计数，避免 N+1 问题。

核心 SQL 使用 INNER JOIN 找到同时存在于两个好友集合中的用户：

```sql
SELECT candidate_id, COUNT(*) AS common_count
FROM (
    SELECT
        cand.id AS candidate_id,
        target_friends.friend_uid AS common_friend_id
    FROM (
        -- 目标用户的好友ID集合
        SELECT friend_id AS friend_uid FROM friendships WHERE user_id = :uid
        UNION
        SELECT user_id AS friend_uid FROM friendships WHERE friend_id = :uid
    ) AS target_friends
    INNER JOIN (
        -- 每个候选用户的好友ID集合
        SELECT u.id,
            CASE WHEN f.user_id = u.id THEN f.friend_id ELSE f.user_id END AS friend_uid
        FROM users u
        INNER JOIN friendships f ON (f.user_id = u.id OR f.friend_id = u.id)
        WHERE u.id IN :cand_ids
    ) AS cand ON target_friends.friend_uid = cand.friend_uid
) AS common
GROUP BY candidate_id
```

| 子查询 | 产出的数据集 |
|--------|------------|
| `target_friends` | 目标用户的所有好友 ID |
| `cand` | 每个候选用户的所有好友 ID |
| `INNER JOIN ON friend_uid` | 匹配共同好友（同时出现在两者集合中） |
| `GROUP BY candidate_id` | 按候选用户分组，COUNT 聚合即为共同好友数 |

### `_batch_common_friends_detail(db, user_id, candidate_ids)` — 共同好友详情

```python
def _batch_common_friends_detail(
    db: Session, user_id: int, candidate_ids: list[int]
) -> dict[int, list[User]]:
```

为每个候选用户返回最多 5 个共同好友的 `User` 对象。用于推荐结果的 `reason.common_friends` 字段展示。

### `_get_friend_ids(db, user_id)` — 获取好友 ID 集合

```python
def _get_friend_ids(db: Session, user_id: int) -> set[int]:
    friendships = db.query(Friendship).filter(
        (Friendship.user_id == user_id) | (Friendship.friend_id == user_id)
    ).all()
    friend_ids = set()
    for f in friendships:
        if f.user_id == user_id:
            friend_ids.add(f.friend_id)
        else:
            friend_ids.add(f.user_id)
    return friend_ids
```

| 属性 | 说明 |
|------|------|
| **用途** | 无向边查询辅助函数，从两列提取所有好友 ID |
| **返回** | `set[int]` — 去重的好友 ID 集合 |

---

## 函数汇总

| 函数 | 可见性 | 说明 |
|------|--------|------|
| `get_recommendations()` | 公共 | 推荐引擎入口：依次调用 CTE、标签匹配、共同好友计数、评分排序、分页、组装返回 |
| `_get_cte_candidates()` | 私有 | CTE 递归查询发现 2~3 度好友 |
| `_get_tag_candidates()` | 私有 | JSON_OVERLAPS 匹配共同兴趣标签的用户 |
| `_batch_common_friends_count()` | 私有 | 一次 SQL 批量计算目标用户与所有候选用户的共同好友数 |
| `_batch_common_friends_detail()` | 私有 | 批量获取共同好友的 User 详情（每候选最多 5 个） |
| `_get_friend_ids()` | 私有 | 获取指定用户的所有好友 ID 集合（处理无向边） |
