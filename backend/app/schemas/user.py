"""
User 相关的 Pydantic 数据模型

请求验证规则：
- username: 必填，3-50位字母数字下划线，去除首尾空格
- tags: 可选，最多10个标签，每个最长30字符
- 响应模型启用 from_attributes=True 支持从 ORM 对象自动转换
"""
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    """用户共用字段"""
    username: str = Field(
        min_length=3, max_length=50,
        description="用户名，字母数字下划线组成"
    )
    nickname: Optional[str] = Field(
        default=None, max_length=100,
        description="显示昵称"
    )
    avatar_url: Optional[str] = Field(
        default=None, max_length=500,
        description="头像图片URL"
    )
    bio: Optional[str] = Field(
        default=None, max_length=500,
        description="个人简介"
    )
    tags: Optional[list[str]] = Field(
        default_factory=list,
        max_length=10,
        description="兴趣标签列表"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """校验用户名格式：去除首尾空格，只允许字母数字下划线"""
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("用户名只能包含字母、数字和下划线，长度3-50")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> list[str]:
        """校验标签：去重，过滤空字符串和纯空格，限制每个标签最长30字符"""
        if v is None:
            return []
        cleaned = []
        seen = set()
        for tag in v:
            tag = tag.strip()
            if not tag:
                continue
            if len(tag) > 30:
                raise ValueError(f"单个标签最多30个字符，超出: {tag}")
            if tag not in seen:
                seen.add(tag)
                cleaned.append(tag)
        if len(cleaned) > 10:
            raise ValueError("标签最多10个")
        return cleaned


class UserCreate(UserBase):
    """创建用户请求体"""
    pass


class UserUpdate(BaseModel):
    """更新用户请求体，所有字段可选（部分更新）"""
    nickname: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[list[str]] = Field(default=None)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """校验标签，允许 None 表示不更新此字段"""
        if v is None:
            return None
        cleaned = []
        seen = set()
        for tag in v:
            tag = tag.strip()
            if not tag:
                continue
            if len(tag) > 30:
                raise ValueError(f"单个标签最多30个字符，超出: {tag}")
            if tag not in seen:
                seen.add(tag)
                cleaned.append(tag)
        if len(cleaned) > 10:
            raise ValueError("标签最多10个")
        return cleaned


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    tags: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    # 允许从 SQLAlchemy ORM 对象直接创建 Pydantic 模型
    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    """用户简要信息（用于好友列表等场景）"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)
