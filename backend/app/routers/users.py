"""
用户相关 RESTful API 路由

端点列表：
- POST   /api/v1/users                          创建用户
- GET    /api/v1/users                          获取用户列表（支持搜索和分页）
- GET    /api/v1/users/{user_id}                 获取单个用户
- PUT    /api/v1/users/{user_id}                 更新用户信息
- DELETE /api/v1/users/{user_id}                 删除用户
- GET    /api/v1/users/{user_id}/friends         获取好友列表
- GET    /api/v1/users/{user_id}/common-friends/{other_id}  获取共同好友
- GET    /api/v1/users/{user_id}/recommendations  获取好友推荐
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserBrief
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services import user_service, friendship_service, recommendation_service

router = APIRouter(prefix="/users", tags=["用户管理"])


# ==================== 基础 CRUD ====================

@router.post("/", response_model=UserResponse, status_code=201, summary="创建用户")
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户

    - **username**: 唯一用户名，3-50位字母数字下划线
    - **tags**: 兴趣标签数组，如 ["Python", "篮球", "摄影"]
    """
    try:
        user = user_service.create_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return user


@router.get("/", response_model=PaginatedResponse[UserResponse], summary="获取用户列表")
def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    keyword: str = Query(default="", description="按昵称或用户名搜索"),
    db: Session = Depends(get_db),
):
    """
    分页获取用户列表，支持按关键词搜索昵称或用户名
    """
    users, total = user_service.get_users_paginated(
        db, page=page, page_size=page_size, keyword=keyword or None
    )
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """根据用户ID获取用户详细信息"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    """
    部分更新用户信息，仅更新传入的非空字段

    支持更新：nickname, avatar_url, bio, tags
    不支持更新 username（用户名不可变更）
    """
    user = user_service.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return user


@router.delete("/{user_id}", response_model=MessageResponse, summary="删除用户")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户及其所有好友关系"""
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return MessageResponse(message=f"用户 {user_id} 已删除")


# ==================== 好友相关查询 ====================

@router.get(
    "/{user_id}/friends",
    response_model=PaginatedResponse[UserBrief],
    summary="获取用户好友列表",
)
def get_user_friends(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取指定用户的所有好友"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")

    friends, total = friendship_service.get_user_friends(
        db, user_id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=friends,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}/common-friends/{other_id}",
    summary="获取两个用户的共同好友",
)
def get_common_friends(
    user_id: int,
    other_id: int,
    db: Session = Depends(get_db),
):
    """
    计算两个用户之间的共同好友

    技术要点：使用 SQL INTERSECT 运算符计算两个好友集合的交集
    """
    if user_id == other_id:
        raise HTTPException(status_code=400, detail="不能与自身比较")

    user_a = user_service.get_user_by_id(db, user_id)
    user_b = user_service.get_user_by_id(db, other_id)
    if not user_a:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    if not user_b:
        raise HTTPException(status_code=404, detail=f"用户ID {other_id} 不存在")

    common_friends = friendship_service.get_common_friends(db, user_id, other_id)
    return {
        "user_a": UserBrief.model_validate(user_a),
        "user_b": UserBrief.model_validate(user_b),
        "common_friends": [UserBrief.model_validate(f) for f in common_friends],
        "count": len(common_friends),
    }


# ==================== 好友推荐 ====================

@router.get(
    "/{user_id}/recommendations",
    summary="获取好友推荐列表",
)
def get_recommendations(
    user_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    max_degree: int = Query(default=3, ge=2, le=3, description="最大好友度数(2或3)"),
    db: Session = Depends(get_db),
):
    """
    获取基于共同好友和兴趣标签的好友推荐

    推荐算法综合三个维度：
    1. **二度/三度好友**（CTE 递归查询）
    2. **共同好友数量**（INTERSECT 计算）
    3. **共同兴趣标签**（JSON_OVERLAPS 匹配）

    评分公式：common_friends_count * 3 + common_tags_count * 2 + (max_degree - degree + 1) * 1
    """
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")

    recommendations, total = recommendation_service.get_recommendations(
        db, user_id, page=page, page_size=page_size, max_degree=max_degree
    )
    return PaginatedResponse(
        items=recommendations,
        total=total,
        page=page,
        page_size=page_size,
    )
