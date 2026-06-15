"""
Friendship 相关的 Pydantic 数据模型

关键逻辑：
- FriendshipCreate 在 model_validator 中规范化 user_id/friend_id 顺序，
  确保 user_id 总是小于 friend_id，调用方无需关心传入顺序
- 校验不能添加自己为好友（user_id != friend_id）
"""
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class FriendshipCreate(BaseModel):
    """创建好友关系请求体"""
    user_id: int = Field(gt=0, description="用户ID")
    friend_id: int = Field(gt=0, description="好友ID")

    @model_validator(mode="after")
    def normalize_ids(self) -> "FriendshipCreate":
        """规范化：确保 user_id < friend_id"""
        if self.user_id == self.friend_id:
            raise ValueError("不能添加自己为好友")
        if self.user_id > self.friend_id:
            # 交换，使较小的ID在 user_id 位置
            self.user_id, self.friend_id = self.friend_id, self.user_id
        return self


class FriendshipResponse(BaseModel):
    """好友关系响应"""
    id: int
    user_id: int
    friend_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendshipExistsResponse(BaseModel):
    """好友关系存在性检查响应"""
    are_friends: bool = Field(description="两人是否为好友")
    friendship_id: int | None = Field(default=None, description="若为好友，返回关系记录ID")
