# Schemas 包初始化

> **源码文件**：`backend/app/schemas/__init__.py`

---

## 文件职责

将 `schemas` 子包中所有 Pydantic 数据模型统一导出，方便其他模块通过 `from app.schemas import X` 简洁导入。

---

## 代码

```python
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserBrief
from app.schemas.friendship import FriendshipCreate, FriendshipResponse, FriendshipExistsResponse
from app.schemas.message import MessageCreate, MessageResponse, ConversationItem, MarkReadResponse
from app.schemas.common import PaginationParams, PaginatedResponse, ErrorResponse, MessageResponse as CommonMessageResponse

__all__ = [
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserBrief",
    "FriendshipCreate", "FriendshipResponse", "FriendshipExistsResponse",
    "MessageCreate", "MessageResponse", "ConversationItem", "MarkReadResponse",
    "PaginationParams", "PaginatedResponse", "ErrorResponse", "CommonMessageResponse",
]
```

---

## 关键细节

### 命名冲突处理

```python
from app.schemas.common import MessageResponse as CommonMessageResponse
```

| 问题 | `common.py` 和 `message.py` 都定义了名为 `MessageResponse` 的类 |
|------|------|
| **冲突** | 两个不同的 `MessageResponse` 类无法同时存在于同一命名空间 |
| **解决** | 将 `common.py` 中的版本用别名 `CommonMessageResponse` 导入 |
| **使用** | 路由中通常直接导入：`from app.schemas.common import MessageResponse` |

### `__all__` 列表

导出的所有模型类分为四组：

| 分组 | 导出的类 | 用途 |
|------|---------|------|
| 用户 | `UserBase`, `UserCreate`, `UserUpdate`, `UserResponse`, `UserBrief` | 用户 CRUD + 好友列表 |
| 好友关系 | `FriendshipCreate`, `FriendshipResponse`, `FriendshipExistsResponse` | 添加/查询/校验好友 |
| 消息 | `MessageCreate`, `MessageResponse`, `ConversationItem`, `MarkReadResponse` | 聊天功能 |
| 通用 | `PaginationParams`, `PaginatedResponse`, `ErrorResponse`, `CommonMessageResponse` | 分页、错误、消息响应 |

---

## 函数汇总

| 变量 | 说明 |
|------|------|
| `__all__` | 控制 `from app.schemas import *` 时导出的 13 个类（用别名重命名冲突的 `MessageResponse` 为 `CommonMessageResponse`） |
