"""
好友关系服务层：好友增删查 + 共同好友计算

技术要点：
- 共同好友使用 MySQL INTERSECT 运算符
- 好友查询使用无向边模式（检查 user_id 和 friend_id 两个方向）
- 所有写操作前校验用户存在性和关系唯一性
"""
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.friendship import Friendship
from app.schemas.friendship import FriendshipCreate
from app.utils.pagination import get_pagination_slice


def create_friendship(db: Session, data: FriendshipCreate) -> Friendship:
    """
    创建无向好友关系

    Args:
        db: 数据库会话
        data: 已规范化（user_id < friend_id）的创建数据

    Returns:
        新创建的 Friendship 对象

    Raises:
        ValueError: 用户不存在或已是好友
    """
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

    friendship = Friendship(
        user_id=data.user_id,
        friend_id=data.friend_id,
    )
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship


def delete_friendship(db: Session, friendship_id: int) -> bool:
    """
    根据关系ID删除好友关系

    Args:
        db: 数据库会话
        friendship_id: 好友关系记录ID

    Returns:
        是否删除成功
    """
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        return False
    db.delete(friendship)
    db.commit()
    return True


def delete_friendship_by_users(db: Session, user_id: int, friend_id: int) -> bool:
    """
    根据两个用户ID删除好友关系

    内部规范化后查找并删除记录

    Args:
        db: 数据库会话
        user_id: 第一个用户ID
        friend_id: 第二个用户ID

    Returns:
        是否删除成功
    """
    # 规范化为较小ID在前
    a, b = (user_id, friend_id) if user_id < friend_id else (friend_id, user_id)
    friendship = db.query(Friendship).filter(
        (Friendship.user_id == a) & (Friendship.friend_id == b)
    ).first()
    if not friendship:
        return False
    db.delete(friendship)
    db.commit()
    return True


def check_friendship_exists(db: Session, user_id: int, other_id: int) -> tuple[bool, Optional[int]]:
    """
    检查两个用户是否为好友关系

    Args:
        db: 数据库会话
        user_id: 第一个用户ID
        other_id: 第二个用户ID

    Returns:
        (是否好友, 关系记录ID或None)
    """
    if user_id == other_id:
        return False, None
    a, b = (user_id, other_id) if user_id < other_id else (other_id, user_id)
    friendship = db.query(Friendship).filter(
        (Friendship.user_id == a) & (Friendship.friend_id == b)
    ).first()
    if friendship:
        return True, friendship.id
    return False, None


def get_user_friends(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    """
    获取指定用户的所有好友（分页）

    由于使用无向边存储（user_id < friend_id），
    需要查询 user_id = X 或 friend_id = X 的所有记录，
    然后获取 "另一端" 的用户对象

    Args:
        db: 数据库会话
        user_id: 目标用户ID
        page: 页码
        page_size: 每页数量

    Returns:
        (好友用户列表, 总数量) 二元组
    """
    # 获取好友ID列表
    # 从 user_id 列获取（此时 friend_id 是好友）
    query_a = db.query(Friendship.friend_id).filter(Friendship.user_id == user_id)
    # 从 friend_id 列获取（此时 user_id 是好友）
    query_b = db.query(Friendship.user_id).filter(Friendship.friend_id == user_id)

    # 合并两个方向的查询
    friend_ids_subquery = query_a.union_all(query_b).subquery()

    # 计数
    total = db.query(friend_ids_subquery).count()

    # 分页获取好友详细信息
    offset, limit = get_pagination_slice(page, page_size)
    friend_ids = (
        db.query(friend_ids_subquery.c[0])
        .order_by(friend_ids_subquery.c[0])
        .offset(offset)
        .limit(limit)
        .all()
    )
    friend_id_list = [row[0] for row in friend_ids]

    if not friend_id_list:
        return [], total

    friends = db.query(User).filter(User.id.in_(friend_id_list)).all()
    # 按原ID顺序排序
    friend_map = {u.id: u for u in friends}
    sorted_friends = [friend_map[fid] for fid in friend_id_list if fid in friend_map]
    return sorted_friends, total


def get_common_friends(db: Session, user_id_a: int, user_id_b: int) -> list[User]:
    """
    使用 SQL INTERSECT 计算两个用户的共同好友

    技术要点：
    1. 分别查询两个用户的好友集合（无向边，需要从两列查找）
    2. 使用 INTERSECT 取两个集合的交集
    3. JOIN users 表获取共同好友的详细信息

    Args:
        db: 数据库会话
        user_id_a: 用户A的ID
        user_id_b: 用户B的ID

    Returns:
        共同好友的用户对象列表
    """
    # 使用原生 SQL 实现 INTERSECT
    # 查询逻辑：
    #   (用户A的好友ID集合) INTERSECT (用户B的好友ID集合)
    sql = text("""
        SELECT u.*
        FROM users u
        WHERE u.id IN (
            -- 用户A的好友ID
            SELECT friend_id FROM friendships WHERE user_id = :uid_a
            UNION
            SELECT user_id FROM friendships WHERE friend_id = :uid_a
        )
        AND u.id IN (
            -- 用户B的好友ID
            SELECT friend_id FROM friendships WHERE user_id = :uid_b
            UNION
            SELECT user_id FROM friendships WHERE friend_id = :uid_b
        )
    """)
    result = db.execute(sql, {"uid_a": user_id_a, "uid_b": user_id_b})
    # 将原生结果行转换为 User ORM 对象
    common_friend_ids = [row[0] for row in result.fetchall()]
    if not common_friend_ids:
        return []
    return db.query(User).filter(User.id.in_(common_friend_ids)).all()
