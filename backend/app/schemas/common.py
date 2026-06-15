"""
通用数据模型：分页参数、错误响应、消息响应
"""
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页查询参数依赖"""
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应包装"""
    items: list[T] = Field(description="当前页数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")

    @property
    def total_pages(self) -> int:
        """计算总页数"""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class ErrorResponse(BaseModel):
    """统一错误响应格式"""
    detail: str = Field(description="错误描述信息")
    status_code: int = Field(description="HTTP 状态码")


class MessageResponse(BaseModel):
    """操作成功消息响应"""
    message: str = Field(description="操作结果消息")
