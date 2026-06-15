"""
User 模型：社交网络用户表

设计要点：
- tags 字段使用 MySQL 原生 JSON 类型存储兴趣标签数组
- username 全局唯一，用于登录
- nickname 用于显示，可在应用内按昵称搜索其他用户
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(
        Integer, primary_key=True, autoincrement=True,
        comment="用户主键ID"
    )
    username = Column(
        String(50), unique=True, nullable=False, index=True,
        comment="唯一用户名，用于登录"
    )
    nickname = Column(
        String(100), default=None,
        comment="显示昵称，支持按昵称搜索"
    )
    avatar_url = Column(
        String(500), default=None,
        comment="头像图片URL"
    )
    bio = Column(
        Text, default=None,
        comment="个人简介"
    )
    # MySQL 原生 JSON 类型，存储字符串数组如 ["Python", "机器学习", "摄影"]
    tags = Column(
        JSON, default=list,
        comment="兴趣标签 JSON 数组"
    )
    created_at = Column(
        DateTime, server_default=func.now(),
        comment="注册时间"
    )
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(),
        comment="最后更新时间"
    )

    __table_args__ = (
        Index("idx_users_nickname", "nickname"),
        Index("idx_users_created_at", "created_at"),
        {"comment": "用户表"},
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', nickname='{self.nickname}')>"
