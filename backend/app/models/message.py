"""
Message 模型：私聊消息表

设计要点：
- sender_id 和 receiver_id 均为 users 表外键，删除用户时级联删除消息
- is_read 使用 MySQL 原生默认值 0，用于未读计数
- 复合索引 (sender_id, receiver_id) 加速会话查询
"""
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func, text
from app.database import Base


class Message(Base):
    """私聊消息表"""

    __tablename__ = "messages"

    id = Column(
        Integer, primary_key=True, autoincrement=True,
        comment="消息主键ID"
    )
    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="发送者用户ID"
    )
    receiver_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="接收者用户ID"
    )
    content = Column(
        Text, nullable=False,
        comment="消息文本内容"
    )
    is_read = Column(
        Boolean, nullable=False,
        server_default=text("0"),
        comment="是否已读（0=未读 1=已读）"
    )
    created_at = Column(
        DateTime, server_default=func.now(),
        comment="消息发送时间"
    )

    __table_args__ = (
        Index("idx_messages_sender_id", "sender_id"),
        Index("idx_messages_receiver_id", "receiver_id"),
        Index("idx_messages_pair", "sender_id", "receiver_id"),
        Index("idx_messages_created_at", "created_at"),
        {"comment": "私聊消息表"},
    )

    def __repr__(self):
        return (
            f"<Message(id={self.id}, sender={self.sender_id}, "
            f"receiver={self.receiver_id}, read={self.is_read})>"
        )
