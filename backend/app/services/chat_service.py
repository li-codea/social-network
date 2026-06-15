"""
聊天服务层：封装消息发送、会话列表、聊天记录、已读标记等业务逻辑

所有函数接收 db 会话作为第一个参数（通过 FastAPI Depends 注入），
不直接处理 HTTP 异常，由路由层决定如何响应
"""
from typing import Optional
from sqlalchemy import func, or_, and_, case, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.models.message import Message
from app.models.user import User
from app.utils.pagination import get_pagination_slice


def send_message(
    db: Session, sender_id: int, receiver_id: int, content: str
) -> Message:
    """
    发送一条私聊消息

    Args:
        db: 数据库会话
        sender_id: 发送者ID
        receiver_id: 接收者ID
        content: 消息文本内容

    Returns:
        新创建的 Message ORM 对象

    Raises:
        ValueError: 发送者或接收者不存在
    """
    if sender_id == receiver_id:
        raise ValueError("不能给自己发送消息")

    # 验证双方用户存在
    sender = db.query(User).filter(User.id == sender_id).first()
    if not sender:
        raise ValueError(f"发送者用户ID {sender_id} 不存在")
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise ValueError(f"接收者用户ID {receiver_id} 不存在")

    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversations(
    db: Session, user_id: int, page: int = 1, page_size: int = 20
) -> tuple[list[dict], int]:
    """
    获取用户的会话列表，按最近消息时间倒序排列

    技术要点：
    - 使用子查询找出每个会话的最新消息和未读计数
    - 通过对 sender_id/receiver_id 与 user_id 的比较确定"对方用户"
    - 排序依据为每个会话的最新消息时间

    Args:
        db: 数据库会话
        user_id: 当前用户ID
        page: 页码
        page_size: 每页数量

    Returns:
        (会话列表, 总数量) 二元组
    """
    # 验证用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"用户ID {user_id} 不存在")

    # 使用原始 SQL：找出与 user_id 有过消息往来的所有对方用户，
    # 以及每个会话的最后消息、最后时间和未读计数
    sql = text("""
        SELECT
            CASE
                WHEN m.sender_id = :uid THEN m.receiver_id
                ELSE m.sender_id
            END AS other_id,
            MAX(m.created_at) AS updated_at,
            SUM(CASE WHEN m.receiver_id = :uid AND m.is_read = 0 THEN 1 ELSE 0 END) AS unread_count
        FROM messages m
        WHERE m.sender_id = :uid OR m.receiver_id = :uid
        GROUP BY other_id
        ORDER BY updated_at DESC
    """)

    result = db.execute(sql, {"uid": user_id})
    all_rows = result.fetchall()

    total = len(all_rows)
    offset, limit = get_pagination_slice(page, page_size)
    page_rows = all_rows[offset:offset + limit]

    if not page_rows:
        return [], total

    # 批量加载对方用户信息
    other_ids = [row.other_id for row in page_rows]
    users_map = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(other_ids)).all()
    }

    # 批量获取每个会话的最后一条消息内容
    last_msg_sql = text("""
        SELECT m.content
        FROM messages m
        WHERE ((m.sender_id = :uid AND m.receiver_id = :oid)
            OR (m.sender_id = :oid AND m.receiver_id = :uid))
        ORDER BY m.created_at DESC
        LIMIT 1
    """)

    conversations = []
    from app.schemas.user import UserBrief

    for row in page_rows:
        other_user = users_map.get(row.other_id)
        if not other_user:
            continue

        # 获取最后一条消息内容
        msg_result = db.execute(
            last_msg_sql, {"uid": user_id, "oid": row.other_id}
        )
        last_msg_row = msg_result.fetchone()
        last_message = last_msg_row.content if last_msg_row else ""

        conversations.append({
            "user": UserBrief.model_validate(other_user),
            "last_message": last_message,
            "unread_count": row.unread_count,
            "updated_at": row.updated_at,
        })

    return conversations, total


def get_chat_history(
    db: Session,
    user_id: int,
    other_id: int,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Message], int]:
    """
    获取两个用户之间的聊天记录，按时间倒序排列（最新在前）

    Args:
        db: 数据库会话
        user_id: 当前用户ID
        other_id: 对方用户ID
        page: 页码
        page_size: 每页数量

    Returns:
        (消息列表, 总数量) 二元组
    """
    if user_id == other_id:
        raise ValueError("不能与自己聊天")

    query = db.query(Message).filter(
        or_(
            and_(Message.sender_id == user_id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == user_id),
        )
    )

    total = query.count()
    offset, limit = get_pagination_slice(page, page_size)
    messages = (
        query.order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return messages, total


def mark_as_read(db: Session, user_id: int, other_id: int) -> int:
    """
    将对方发送给当前用户的所有未读消息标记为已读

    Args:
        db: 数据库会话
        user_id: 当前用户ID（接收者）
        other_id: 对方用户ID（发送者）

    Returns:
        被标记为已读的消息数量
    """
    count = (
        db.query(Message)
        .filter(
            Message.sender_id == other_id,
            Message.receiver_id == user_id,
            Message.is_read == False,
        )
        .count()
    )

    if count > 0:
        db.query(Message).filter(
            Message.sender_id == other_id,
            Message.receiver_id == user_id,
            Message.is_read == False,
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()

    return count
