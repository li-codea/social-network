"""
Message 相关的 Pydantic 数据模型

请求验证规则：
- sender_id != receiver_id（不能给自己发消息）
- content 长度 1-5000 字符
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict
from app.schemas.user import UserBrief


class MessageCreate(BaseModel):
    """发送消息请求体"""
    sender_id: int = Field(gt=0, description="发送者用户ID")
    receiver_id: int = Field(gt=0, description="接收者用户ID")
    content: str = Field(
        min_length=1, max_length=5000,
        description="消息文本内容"
    )

    @model_validator(mode="after")
    def check_not_self(self):
        """校验不能给自己发消息"""
        if self.sender_id == self.receiver_id:
            raise ValueError("不能给自己发送消息")
        return self


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationItem(BaseModel):
    """会话列表项"""
    user: UserBrief
    last_message: str
    unread_count: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkReadResponse(BaseModel):
    """标记已读响应"""
    marked_count: int
    message: str
