# 服务层：好友关系业务逻辑

> **源码文件**：`backend/app/services/friendship_service.py`

---

## 文件职责

封装好友关系的核心业务逻辑：创建、删除（按 ID / 按用户对）、存在性检查、获取好友列表（分页）、共同好友计算（INTERSECT）。

---

## 导入依赖

```python
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.friendship import Friendship
from app.schemas.friendship import FriendshipCreate
from app.utils.pagination import get_pagination_slice
```

---

## 函数详解

### `create_friendship(db, data)` — 创建好友关系

```python
def create_friendship(db: Session, data: FriendshipCreate) -> Friendship:
    # 验证两个用户都存在
    user = db.query(User).filter(User.id == data.user_id).first()
    friend = db.query(User).filter(User.id == data.friend_id).first()
    if not user:
        raise ValueError(f"用户ID {data.user_id} 不存在")
    if not friend:
        raise ValueError(f"用户ID {data.friend_id} 不存在")

    # 检查是否已存在好友关系
    existing = db.query(Friendship).filter(
        (Friendship.user_id == data.user_id) & (Friendship.friend_id == data.friend_id)
    ).first()
    if existing:
        raise ValueError("两人已经是好友关系")

    friendship = Friendship(user_id=data.user_id, friend_id=data.friend_id)
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship
```

| 参数 | 说明 |
|------|------|
| `data` | 经过 `normalize_ids` 校验的创建数据，`user_id < friend_id` 已保证 |

**三重校验**：

| 步骤 | 校验 | 异常 |
|------|------|------|
| 1 | 用户 A 是否存在 | `ValueError` |
| 2 | 用户 B 是否存在 | `ValueError` |
| 3 | 两人是否已经是好友 | `ValueError` |
| 4 | ✅ 通过 → 创建关系 | — |

### `delete_friendship(db, friendship_id)` — 按 ID 删除

```python
def delete_friendship(db: Session, friendship_id: int) -> bool:
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        return False
    db.delete(friendship)
    db.commit()
    return True
```

| 参数 | 说明 |
|------|------|
| `friendship_id` | 好友关系记录的主键 ID |
| **返回** | `True` 删除成功，`False` 记录不存在 |

### `delete_friendship_by_users(db, user_id, friend_id)` — 按用户对删除

```python
def delete_friendship_by_users(db: Session, user_id: int, friend_id: int) -> bool:
    a, b = (user_id, friend_id) if user_id < friend_id else (friend_id, user_id)
    friendship = db.query(Friendship).filter(
        (Friendship.user_id == a) & (Friendship.friend_id == b)
    ).first()
    if not friendship:
        return False
    db.delete(friendship)
    db.commit()
    return True
```

| 关键步骤 | 说明 |
|----------|------|
| `a, b` 的赋值 | 三元表达式自动规范化 ID 顺序，确保查询到唯一的关系记录 |

> 与 `delete_friendship` 的区别：调用方无需知道关系记录 ID，直接传入两个用户 ID 即可。

### `check_friendship_exists(db, user_id, other_id)` — 检查是否为好友

```python
def check_friendship_exists(db: Session, user_id: int, other_id: int) -> tuple[bool, Optional[int]]:
    if user_id == other_id:
        return False, None
    a, b = (user_id, other_id) if user_id < other_id else (other_id, user_id)
    friendship = db.query(Friendship).filter(
        (Friendship.user_id == a) & (Friendship.friend_id == b)
    ).first()
    if friendship:
        return True, friendship.id
    return False, None
```

| 返回 | 含义 |
|------|------|
| `(True, 3)` | 是好友，关系记录 ID 为 3 |
| `(False, None)` | 不是好友（或自己检查自己） |

**边界情况**：`user_id == other_id` 时直接返回 `(False, None)`，不查询数据库。

### `get_user_friends(db, user_id, page, page_size)` — 获取好友列表（分页）

```python
def get_user_friends(
    db: Session, user_id: int,
    page: int = 1, page_size: int = 20,
) -> tuple[list[User], int]:
```

这是最具"无向边"特色的查询：

**步骤 1：从两个方向获取好友 ID**

```python
query_a = db.query(Friendship.friend_id).filter(Friendship.user_id == user_id)
query_b = db.query(Friendship.user_id).filter(Friendship.friend_id == user_id)
friend_ids_subquery = query_a.union_all(query_b).subquery()
```

| 子查询 | 方向 | SQL 等价 |
|--------|------|----------|
| `query_a` | 用户是较小的 ID | `SELECT friend_id FROM friendships WHERE user_id = X` |
| `query_b` | 用户是较大的 ID | `SELECT user_id FROM friendships WHERE friend_id = X` |
| `union_all` | 合并 | 合并两个方向的所有好友 ID |
| `.subquery()` | 转为子查询 | 包装为嵌套 SELECT 供外层使用 |

**步骤 2：计数和分页**

```python
total = db.query(friend_ids_subquery).count()
offset, limit = get_pagination_slice(page, page_size)
friend_ids = (
    db.query(friend_ids_subquery.c[0])
    .order_by(friend_ids_subquery.c[0])
    .offset(offset).limit(limit).all()
)
friend_id_list = [row[0] for row in friend_ids]
```

**步骤 3：加载好友详细信息并按 ID 顺序排列**

```python
friends = db.query(User).filter(User.id.in_(friend_id_list)).all()
friend_map = {u.id: u for u in friends}
sorted_friends = [friend_map[fid] for fid in friend_id_list if fid in friend_map]
return sorted_friends, total
```

使用字典映射确保结果的顺序与子查询中 ID 的顺序一致。

### `get_common_friends(db, user_id_a, user_id_b)` — 计算共同好友

```python
def get_common_friends(db: Session, user_id_a: int, user_id_b: int) -> list[User]:
```

核心 SQL 使用了双重 IN 子查询实现交集：

```sql
SELECT u.*
FROM users u
WHERE u.id IN (
    -- 用户A的好友ID集合
    SELECT friend_id FROM friendships WHERE user_id = :uid_a
    UNION
    SELECT user_id FROM friendships WHERE friend_id = :uid_a
)
AND u.id IN (
    -- 用户B的好友ID集合
    SELECT friend_id FROM friendships WHERE user_id = :uid_b
    UNION
    SELECT user_id FROM friendships WHERE friend_id = :uid_b
)
```

| 技术 | 说明 |
|------|------|
| `UNION`（非 `UNION ALL`） | 取并集且自动去重 |
| 双重 `IN` | 两个集合的交集——ID 必须同时在 A 的好友集合和 B 的好友集合中 |
| 无向边处理 | 每个用户的子查询都从 `user_id` 和 `friend_id` 两列查找 |

**等价数学表达**：`friends(A) ∩ friends(B)`

---

## 函数汇总

| 函数 | 参数 | 返回 | 可能异常 |
|------|------|------|----------|
| `create_friendship()` | `db, data` | `Friendship` ORM 对象 | `ValueError`：用户不存在或已是好友 |
| `delete_friendship()` | `db, friendship_id` | `bool` | 无 |
| `delete_friendship_by_users()` | `db, user_id, friend_id` | `bool` | 无 |
| `check_friendship_exists()` | `db, user_id, other_id` | `(bool, int\|None)` | 无 |
| `get_user_friends()` | `db, user_id, page, page_size` | `(list[User], int)` | 无 |
| `get_common_friends()` | `db, user_id_a, user_id_b` | `list[User]` | 无 |
