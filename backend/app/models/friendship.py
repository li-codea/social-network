"""
Friendship 模型：无向好友关系表

关键约束：
- user_id < friend_id 由 CHECK 约束强制执行
- (user_id, friend_id) 组合唯一，防止重复关系
- 查询用户 X 的所有好友时，需同时检查 user_id = X 和 friend_id = X
  示例 SQL: SELECT * FROM friendships WHERE user_id = X OR friend_id = X
"""
from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index,
)
from sqlalchemy.sql import func
from app.database import Base


class Friendship(Base):
    """无向好友关系表"""

    __tablename__ = "friendships"

    id = Column(
        Integer, primary_key=True, autoincrement=True,
        comment="关系主键ID"
    )
    # user_id 始终存储两个用户中 ID 较小的那个
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="较小ID的用户"
    )
    # friend_id 始终存储两个用户中 ID 较大的那个
    friend_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="较大ID的用户"
    )
    created_at = Column(
        DateTime, server_default=func.now(),
        comment="好友关系建立时间"
    )

    __table_args__ = (
        # 确保每对用户之间只有一条好友记录
        UniqueConstraint("user_id", "friend_id", name="uq_friendship_pair"),
        # 确保 user_id 始终小于 friend_id
        CheckConstraint("user_id < friend_id", name="ck_user_lt_friend"),
        Index("idx_friendship_user_id", "user_id"),
        Index("idx_friendship_friend_id", "friend_id"),
        {"comment": "无向好友关系表，user_id < friend_id 约束保证唯一性"},
    )

    def __repr__(self):
        return f"<Friendship(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id})>"
