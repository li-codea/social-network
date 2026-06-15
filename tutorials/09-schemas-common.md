# Schema：通用数据模型

> **源码文件**：`backend/app/schemas/common.py`

---

## 文件职责

定义项目中通用的 Pydantic 数据模型：分页参数、分页响应包装、错误响应格式、操作成功消息响应。被所有路由模块复用。

---

## 导入依赖

```python
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")
```

| 导入项 | 用途 |
|--------|------|
| `Generic` | 使类支持泛型参数 |
| `TypeVar` | 定义泛型类型变量 `T` |
| `BaseModel` | Pydantic 模型的基类 |
| `Field` | 为模型字段添加描述和校验约束 |

---

## 类详解

### `PaginationParams` — 分页查询参数

```python
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
```

| 字段 | 类型 | 默认值 | 校验规则 | 说明 |
|------|------|--------|----------|------|
| `page` | `int` | `1` | `ge=1`（≥1） | 页码从 1 开始 |
| `page_size` | `int` | `20` | `ge=1, le=100`（1~100） | 限制每页最多 100 条 |

> **注意**：此模型在当前路由中未直接使用（路由中通过 `Query()` 直接声明分页参数），但作为可复用的依赖模型被导出。

### `PaginatedResponse` — 通用分页响应

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(description="当前页数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
```

| 特征 | 说明 |
|------|------|
| **泛型** | `Generic[T]` — `T` 可以是任何模型（`UserResponse`、`MessageResponse` 等） |
| **使用示例** | `PaginatedResponse[UserResponse]` 表示一页用户数据 |
| **`items`** | 泛型列表，存放当前页的实际数据 |
| **`total`** | 总记录数（不是当前页数量），前端用于计算总页数 |

#### `total_pages(self) -> int` — 计算总页数

```python
@property
def total_pages(self) -> int:
    if self.page_size <= 0:
        return 0
    return (self.total + self.page_size - 1) // self.page_size
```

| 属性 | 说明 |
|------|------|
| **装饰器** | `@property` — 作为属性访问而非方法调用 |
| **公式** | 向上取整整数除法：`(总数 + 每页数 - 1) // 每页数` |
| **边界处理** | `page_size <= 0` 时返回 0，防止除零错误 |

**分页计算示例**：

| total | page_size | total_pages | 计算公式 |
|-------|-----------|-------------|----------|
| 100 | 20 | 5 | `(100 + 19) // 20 = 5` |
| 101 | 20 | 6 | `(101 + 19) // 20 = 6` |
| 0 | 20 | 0 | `(0 + 19) // 20 = 0` |

### `ErrorResponse` — 统一错误响应

```python
class ErrorResponse(BaseModel):
    detail: str = Field(description="错误描述信息")
    status_code: int = Field(description="HTTP 状态码")
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail` | `str` | 人类可读的错误描述 |
| `status_code` | `int` | HTTP 状态码（如 404、409） |

> **注意**：此模型目前被导出但未在路由中显式使用。FastAPI 的 `HTTPException` 会自动生成符合标准的错误 JSON。

### `MessageResponse` — 操作成功消息

```python
class MessageResponse(BaseModel):
    message: str = Field(description="操作结果消息")
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | `str` | 成功操作的结果消息文本 |

**使用场景**：删除操作、解除好友操作等不需要返回实体数据的接口。

示例响应：`{"message": "用户 5 已删除"}`

---

## 函数汇总

| 函数/方法 | 类型 | 说明 |
|-----------|------|------|
| `PaginatedResponse.total_pages()` | `@property` 计算属性 | 使用向上取整除法计算总页数 |
| `PaginationParams.__init__()` | 构造函数（继承） | 默认 page=1, page_size=20 |
| `PaginatedResponse.__init__()` | 构造函数（继承） | 接受 items, total, page, page_size |
| `ErrorResponse.__init__()` | 构造函数（继承） | 接受 detail, status_code |
| `MessageResponse.__init__()` | 构造函数（继承） | 接受 message |
