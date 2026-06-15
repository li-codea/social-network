"""
用户服务层：封装用户相关的业务逻辑

所有函数接收 db 会话作为第一个参数（通过 FastAPI Depends 注入），
不直接处理 HTTP 异常，由路由层决定如何响应
"""
from typing import Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.friendship import Friendship
from app.schemas.user import UserCreate, UserUpdate
from app.utils.pagination import get_pagination_slice


def create_user(db: Session, data: UserCreate) -> User:
    """
    创建新用户

    Args:
        db: 数据库会话
        data: 经过 Pydantic 校验的创建数据

    Returns:
        新创建的 User ORM 对象

    Raises:
        ValueError: username 已被占用
    """
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise ValueError(f"用户名 '{data.username}' 已被占用")

    user = User(
        username=data.username,
        nickname=data.nickname,
        avatar_url=data.avatar_url,
        bio=data.bio,
        tags=data.tags or [],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户，不存在则返回 None"""
    return db.query(User).filter(User.id == user_id).first()


def get_users_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
) -> tuple[list[User], int]:
    """
    分页获取用户列表，支持按昵称或用户名搜索

    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        keyword: 搜索关键词，匹配昵称或用户名（LIKE %keyword%）

    Returns:
        (用户列表, 总数量) 二元组
    """
    query = db.query(User)
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                User.nickname.like(like_pattern),
                User.username.like(like_pattern),
            )
        )

    total = query.count()
    offset, limit = get_pagination_slice(page, page_size)
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return users, total


def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
    """
    部分更新用户信息

    Args:
        db: 数据库会话
        user_id: 用户ID
        data: 更新数据，只更新非 None 字段

    Returns:
        更新后的 User 对象，不存在则返回 None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # 仅更新显式传入的字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """
    删除用户，同时级联删除相关好友关系

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        是否删除成功（用户不存在时返回 False）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # 删除与该用户相关的所有好友关系
    db.query(Friendship).filter(
        (Friendship.user_id == user_id) | (Friendship.friend_id == user_id)
    ).delete()

    # 删除用户自身
    db.delete(user)
    db.commit()
    return True
