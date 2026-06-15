"""
聊天相关 RESTful API 路由

端点列表：
- POST   /api/v1/messages/                          发送消息
- GET    /api/v1/messages/conversations?user_id=X    获取会话列表
- GET    /api/v1/messages/?user_id=X&other_id=Y      获取聊天记录
- PUT    /api/v1/messages/read?user_id=X&other_id=Y  标记已读
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    ConversationItem,
    MarkReadResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import chat_service

router = APIRouter(prefix="/messages", tags=["消息管理"])


@router.post("/", response_model=MessageResponse, status_code=201, summary="发送消息")
def send_message(data: MessageCreate, db: Session = Depends(get_db)):
    """
    发送一条私聊消息

    - **sender_id**: 发送者用户ID
    - **receiver_id**: 接收者用户ID
    - **content**: 消息文本内容（1-5000字符）
    """
    try:
        message = chat_service.send_message(
            db,
            sender_id=data.sender_id,
            receiver_id=data.receiver_id,
            content=data.content,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return message


@router.get(
    "/conversations",
    response_model=PaginatedResponse[ConversationItem],
    summary="获取会话列表",
)
def list_conversations(
    user_id: int = Query(gt=0, description="当前用户ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取用户的会话列表，按最近消息时间倒序排列

    每条会话包含：对方用户信息、最后一条消息预览、未读计数
    """
    try:
        conversations, total = chat_service.get_conversations(
            db, user_id=user_id, page=page, page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PaginatedResponse(
        items=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/", response_model=PaginatedResponse[MessageResponse], summary="获取聊天记录")
def get_messages(
    user_id: int = Query(gt=0, description="当前用户ID"),
    other_id: int = Query(gt=0, description="对方用户ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取两个用户之间的聊天记录，按时间倒序排列（最新消息在前）
    """
    try:
        messages, total = chat_service.get_chat_history(
            db, user_id=user_id, other_id=other_id, page=page, page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PaginatedResponse(
        items=messages,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/read", response_model=MarkReadResponse, summary="标记消息已读")
def mark_read(
    user_id: int = Query(gt=0, description="当前用户ID（接收者）"),
    other_id: int = Query(gt=0, description="对方用户ID（发送者）"),
    db: Session = Depends(get_db),
):
    """
    将对方发送给当前用户的所有未读消息标记为已读

    返回被标记的消息数量
    """
    count = chat_service.mark_as_read(db, user_id=user_id, other_id=other_id)
    return MarkReadResponse(
        marked_count=count,
        message=f"已将 {count} 条消息标记为已读",
    )
