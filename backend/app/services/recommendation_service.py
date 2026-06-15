"""
好友推荐引擎：综合三种高级 SQL 技术生成推荐列表

技术要点：
1. CTE 递归查询 — 发现二度/三度好友网络
2. JSON_OVERLAPS — 基于共同兴趣标签匹配用户
3. 共同好友计数 — 通过聚合查询批量计算
4. 加权评分排序 — 综合多维度信号

评分公式：
    score = common_friends_count * 3
          + common_tags_count * 2
          + (max_degree - degree + 1) * 1
"""
from collections import defaultdict
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.friendship import Friendship
from app.utils.pagination import get_pagination_slice


def get_recommendations(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    max_degree: int = 3,
) -> tuple[list[dict], int]:
    """
    为指定用户生成好友推荐列表

    推荐流程：
    1. 通过 CTE 递归查询发现二度和三度好友
    2. 用 JSON_OVERLAPS 查找有共同兴趣标签的非好友用户
    3. 合并候选集，计算每个候选人的评分
    4. 按评分降序排序，分页返回

    Args:
        db: 数据库会话
        user_id: 目标用户ID
        page: 页码
        page_size: 每页数量
        max_degree: 查询的最大好友度数（2 或 3）

    Returns:
        (推荐项列表, 总数量) 二元组
        每个推荐项包含：user, score, reason(common_friends_count, common_friends, common_tags, degree)
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return [], 0

    target_tags = target_user.tags or []

    # ========== 1. CTE 递归查询：二度/三度好友 ==========
    cte_candidates = _get_cte_candidates(db, user_id, max_degree)

    # ========== 2. JSON_OVERLAPS：标签匹配用户 ==========
    tag_candidates = _get_tag_candidates(db, user_id, target_tags)

    # ========== 3. 合并候选集（按ID去重） ==========
    all_candidates = {}  # candidate_id -> {degree, source}
    for cand in cte_candidates:
        all_candidates[cand["id"]] = cand
    for cand in tag_candidates:
        if cand["id"] not in all_candidates:
            cand["degree"] = None  # 纯标签匹配，无度数关系
            all_candidates[cand["id"]] = cand
        else:
            # 已在 CTE 结果中，补充标签匹配信息
            all_candidates[cand["id"]]["common_tags_count"] = cand.get(
                "common_tags_count", 0
            )

    if not all_candidates:
        return [], 0

    # ========== 4. 批量计算共同好友数量 ==========
    candidate_ids = list(all_candidates.keys())
    common_friends_map = _batch_common_friends_count(db, user_id, candidate_ids)

    # ========== 5. 评分排序 ==========
    scored = []
    for cand_id, cand in all_candidates.items():
        common_friends_count = common_friends_map.get(cand_id, 0)
        common_tags_count = cand.get("common_tags_count", 0)
        degree = cand.get("degree", max_degree + 1)  # 纯标签匹配的默认度数

        # 加权评分公式
        score = (
            common_friends_count * 3
            + common_tags_count * 2
            + (max_degree - degree + 1) * 1
        )

        scored.append({
            "candidate_id": cand_id,
            "score": score,
            "common_friends_count": common_friends_count,
            "common_tags_count": common_tags_count,
            "degree": degree,
        })

    # 按评分降序，评分相同的按度数升序
    scored.sort(key=lambda x: (-x["score"], x["degree"]))

    # ========== 6. 分页 ==========
    total = len(scored)
    offset, limit = get_pagination_slice(page, page_size)
    page_candidates = scored[offset:offset + limit]

    if not page_candidates:
        return [], total

    # ========== 7. 加载用户详情并组装返回 ==========
    page_ids = [c["candidate_id"] for c in page_candidates]
    users_map = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(page_ids)).all()
    }

    # 批量获取共同好友详情（前5个）
    common_friends_detail = _batch_common_friends_detail(
        db, user_id, page_ids
    )

    from app.schemas.user import UserBrief

    recommendations = []
    for c in page_candidates:
        cand_user = users_map.get(c["candidate_id"])
        if not cand_user:
            continue

        rec = {
            "user": UserBrief.model_validate(cand_user),
            "score": c["score"],
            "reason": {
                "common_friends_count": c["common_friends_count"],
                "common_friends": [
                    UserBrief.model_validate(f)
                    for f in common_friends_detail.get(c["candidate_id"], [])[:5]
                ],
                "common_tags_count": c["common_tags_count"],
                "common_tags": list(
                    set(target_tags)
                    & set(cand_user.tags or [])
                ),
                "degree": c["degree"],
            },
        }
        recommendations.append(rec)

    return recommendations, total


def _get_cte_candidates(
    db: Session, user_id: int, max_degree: int
) -> list[dict]:
    """
    CTE 递归查询：发现目标用户的二度和三度好友

    使用 MySQL WITH RECURSIVE 从目标用户出发，
    沿着无向好友边向外扩展 2-3 跳，
    排除目标用户自身和已是一度好友的用户

    SQL 技术说明：
    - BASE CASE: 查询用户的所有一度好友（user_id = X OR friend_id = X）
    - RECURSIVE STEP: 从当前已访问节点向外扩展一跳
    - 过滤：排除自身、排除一度好友、只保留 degree >= 2
    - DISTINCT + MIN(degree): 若有多个路径到达同一用户，取最短路径
    """
    sql = text("""
        WITH RECURSIVE friend_graph AS (
            -- BASE CASE: 目标用户的一度好友
            SELECT
                CASE
                    WHEN user_id = :uid THEN friend_id
                    ELSE user_id
                END AS connected_id,
                1 AS degree
            FROM friendships
            WHERE user_id = :uid OR friend_id = :uid

            UNION ALL

            -- RECURSIVE STEP: 从当前节点向外扩展一跳
            SELECT
                CASE
                    WHEN f.user_id = fg.connected_id THEN f.friend_id
                    ELSE f.user_id
                END AS connected_id,
                fg.degree + 1 AS degree
            FROM friendships f
            INNER JOIN friend_graph fg
                ON (f.user_id = fg.connected_id OR f.friend_id = fg.connected_id)
            WHERE fg.degree < :max_deg
        )
        SELECT DISTINCT
            fg.connected_id AS id,
            MIN(fg.degree) AS shortest_degree
        FROM friend_graph fg
        WHERE fg.connected_id != :uid
          AND fg.connected_id NOT IN (
              -- 排除已是一度好友的用户
              SELECT
                  CASE WHEN user_id = :uid THEN friend_id ELSE user_id END
              FROM friendships
              WHERE user_id = :uid OR friend_id = :uid
          )
          AND fg.degree BETWEEN 2 AND :max_deg
        GROUP BY fg.connected_id
        ORDER BY shortest_degree ASC
    """)
    result = db.execute(
        sql,
        {"uid": user_id, "max_deg": max_degree},
    )
    candidates = []
    for row in result.fetchall():
        candidates.append({
            "id": row[0],
            "degree": row[1],
            "common_tags_count": 0,  # 稍后填充
        })
    return candidates


def _get_tag_candidates(
    db: Session, user_id: int, target_tags: list[str]
) -> list[dict]:
    """
    基于 JSON_OVERLAPS 的兴趣标签匹配

    使用 MySQL 8.0 的 JSON_OVERLAPS 函数查找与目标用户
    有至少一个共同兴趣标签的其他用户

    SQL 技术说明：
    - JSON_OVERLAPS(tags_a, tags_b) 返回 1 如果两个 JSON 数组有交集
    - 排除目标用户自身和已是一度好友的用户
    - 在 Python 中计算具体重叠标签数（比纯 SQL 更简洁）
    """
    if not target_tags:
        return []

    import json
    # 将标签数组转为 JSON 数组字符串供 MySQL 使用
    tags_json = json.dumps(target_tags, ensure_ascii=False)

    sql = text("""
        SELECT u.id, u.nickname, u.avatar_url, u.tags
        FROM users u
        WHERE u.id != :uid
          AND u.tags IS NOT NULL
          AND JSON_OVERLAPS(u.tags, CAST(:target_tags AS JSON)) = 1
          AND u.id NOT IN (
              -- 排除已是一度好友的用户
              SELECT
                  CASE WHEN user_id = :uid THEN friend_id ELSE user_id END
              FROM friendships
              WHERE user_id = :uid OR friend_id = :uid
          )
        LIMIT 100
    """)
    result = db.execute(
        sql,
        {"uid": user_id, "target_tags": tags_json},
    )
    candidates = []
    for row in result.fetchall():
        cand_tags = row[3] if row[3] else []
        # 在 Python 中计算交集数量（比 SQL JSON 函数更可维护）
        common_count = len(set(target_tags) & set(cand_tags))
        candidates.append({
            "id": row[0],
            "degree": None,  # 纯标签匹配，非图谱推荐
            "common_tags_count": common_count,
        })
    return candidates


def _batch_common_friends_count(
    db: Session, user_id: int, candidate_ids: list[int]
) -> dict[int, int]:
    """
    批量计算目标用户与每个候选用户的共同好友数量

    使用 UNION ALL + GROUP BY + HAVING 的技术方案，
    一次查询即可完成全部计算，避免 N+1 问题

    SQL 技术说明：
    - 将目标用户的好友ID和每个候选用户的好友ID放入同一个结果集
    - 按 friend_id GROUP BY，HAVING COUNT(*) >= 2 表示该用户同时是两者的好友
    - 使用子查询为每个候选人单独计数
    """
    if not candidate_ids:
        return {}

    # 为每个候选用户计算与目标用户的共同好友数
    sql = text("""
        SELECT
            candidate_id,
            COUNT(*) AS common_count
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
                SELECT
                    u.id,
                    CASE WHEN f.user_id = u.id THEN f.friend_id ELSE f.user_id END AS friend_uid
                FROM users u
                INNER JOIN friendships f
                    ON (f.user_id = u.id OR f.friend_id = u.id)
                WHERE u.id IN :cand_ids
            ) AS cand ON target_friends.friend_uid = cand.friend_uid
        ) AS common
        GROUP BY candidate_id
    """)
    result = db.execute(
        sql,
        {"uid": user_id, "cand_ids": tuple(candidate_ids)},
    )
    common_map = {}
    for row in result.fetchall():
        common_map[row[0]] = row[1]
    # 没有共同好友的默认返回 0
    for cid in candidate_ids:
        if cid not in common_map:
            common_map[cid] = 0
    return common_map


def _batch_common_friends_detail(
    db: Session, user_id: int, candidate_ids: list[int]
) -> dict[int, list[User]]:
    """
    批量获取目标用户与候选用户的共同好友详细信息

    为每个候选用户返回共同好友的 User 对象列表，
    用于在推荐结果的 reason 中展示

    Args:
        db: 数据库会话
        user_id: 目标用户ID
        candidate_ids: 候选用户ID列表

    Returns:
        {candidate_id: [User对象列表]} 的映射
    """
    if not candidate_ids:
        return {}

    detail_map = defaultdict(list)
    target_friend_ids = _get_friend_ids(db, user_id)

    for cand_id in candidate_ids:
        cand_friend_ids = _get_friend_ids(db, cand_id)
        common_ids = target_friend_ids & cand_friend_ids
        if common_ids:
            users = db.query(User).filter(User.id.in_(common_ids)).limit(5).all()
            detail_map[cand_id] = users

    return dict(detail_map)


def _get_friend_ids(db: Session, user_id: int) -> set[int]:
    """
    获取指定用户的所有好友ID集合

    无向边查询辅助函数：同时从 user_id 和 friend_id 两列查找
    """
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
