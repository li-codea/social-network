"""
好友关系相关 RESTful API 路由

端点列表：
- POST   /api/v1/friendships          创建好友关系
- DELETE /api/v1/friendships/{id}      根据关系ID删除
- DELETE /api/v1/friendships/users    根据两个用户ID删除
- GET    /api/v1/friendships/exists    检查两个用户是否为好友
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.friendship import (
    FriendshipCreate,
    FriendshipResponse,
    FriendshipExistsResponse,
)
from app.schemas.common import MessageResponse
from app.services import friendship_service

router = APIRouter(prefix="/friendships", tags=["好友关系管理"])


@router.post(
    "/",
    response_model=FriendshipResponse,
    status_code=201,
    summary="添加好友关系",
)
def add_friendship(data: FriendshipCreate, db: Session = Depends(get_db)):
    """
    建立两个用户之间的好友关系
    内部自动规范化 user_id/friend_id 顺序，调用方无需关心大小关系
    用户不能添加自己为好友
    """
    try:
        friendship = friendship_service.create_friendship(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return friendship


@router.delete(
    "/users",
    response_model=MessageResponse,
    summary="根据用户ID解除好友关系",
)
def remove_friendship_by_users(
    user_id: int = Query(gt=0, description="用户ID"),
    friend_id: int = Query(gt=0, description="好友ID"),
    db: Session = Depends(get_db),
):
    """根据两个用户ID直接解除好友关系"""
    if user_id == friend_id:
        raise HTTPException(status_code=400, detail="不能对自身执行此操作")
    success = friendship_service.delete_friendship_by_users(db, user_id, friend_id)
    if not success:
        raise HTTPException(status_code=404, detail="未找到该好友关系")
    return MessageResponse(message=f"用户 {user_id} 与 {friend_id} 的好友关系已解除")


@router.delete(
    "/{friendship_id}",
    response_model=MessageResponse,
    summary="根据关系ID解除好友",
)
def remove_friendship_by_id(friendship_id: int, db: Session = Depends(get_db)):
    """通过好友关系记录ID删除好友关系"""
    success = friendship_service.delete_friendship(db, friendship_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"好友关系ID {friendship_id} 不存在")
    return MessageResponse(message=f"好友关系 {friendship_id} 已解除")


@router.get(
    "/exists",
    response_model=FriendshipExistsResponse,
    summary="检查好友关系是否存在",
)
def check_friendship(
    user_id: int = Query(gt=0, description="用户ID"),
    other_id: int = Query(gt=0, description="另一用户ID"),
    db: Session = Depends(get_db),
):
    """检查两个用户之间是否已经是好友关系"""
    are_friends, friendship_id = friendship_service.check_friendship_exists(
        db, user_id, other_id
    )
    return FriendshipExistsResponse(are_friends=are_friends, friendship_id=friendship_id)
