# Schema：消息数据模型

> **源码文件**：`backend/app/schemas/message.py`

---

## 文件职责

定义聊天消息相关的 Pydantic 数据模型：发送消息请求、消息响应、会话列表项、已读标记响应。包含发送者/接收者校验、消息长度限制等验证规则。

---

## 导入依赖

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict
from app.schemas.user import UserBrief
```

---

## 类详解

### `MessageCreate` — 发送消息请求体

```python
class MessageCreate(BaseModel):
    sender_id: int = Field(gt=0, description="发送者用户ID")
    receiver_id: int = Field(gt=0, description="接收者用户ID")
    content: str = Field(min_length=1, max_length=5000, description="消息文本内容")
```

| 字段 | 校验规则 | 说明 |
|------|----------|------|
| `sender_id` | `gt=0` | 发送者 ID，必须为正整数 |
| `receiver_id` | `gt=0` | 接收者 ID，必须为正整数 |
| `content` | `min_length=1, max_length=5000` | 消息内容，1~5000 字符 |

#### `check_not_self(self)` — 防止自己给自己发消息

```python
@model_validator(mode="after")
def check_not_self(self):
    if self.sender_id == self.receiver_id:
        raise ValueError("不能给自己发送消息")
    return self
```

| 属性 | 说明 |
|------|------|
| **装饰器** | `@model_validator(mode="after")` — 模型级后置校验 |
| **触发时机** | 所有字段校验通过后 |
| **校验逻辑** | `sender_id == receiver_id` 时抛出 ValueError |
| **返回值** | 校验通过后返回 `self` |

与 `FriendshipCreate.normalize_ids` 不同，这里没有交换逻辑——消息的发送者和接收者是有向的，不能交换。

### `MessageResponse` — 消息响应

```python
class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` | 消息主键 |
| `sender_id` | `int` | 发送者 ID |
| `receiver_id` | `int` | 接收者 ID |
| `content` | `str` | 消息文本 |
| `is_read` | `bool` | 是否已读 |
| `created_at` | `datetime` | 发送时间 |

`from_attributes=True` 允许从 SQLAlchemy `Message` ORM 对象直接转换。

### `ConversationItem` — 会话列表项

```python
class ConversationItem(BaseModel):
    user: UserBrief
    last_message: str
    unread_count: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `user` | `UserBrief` | 对方用户的简要信息 |
| `last_message` | `str` | 最后一条消息的内容预览 |
| `unread_count` | `int` | 该会话中当前用户未读的消息数量 |
| `updated_at` | `datetime` | 会话最后更新时间（最后一条消息的时间） |

**设计说明**：`ConversationItem` 不是一个 ORM 表的直接映射，而是 `chat_service.get_conversations()` 中通过原始 SQL 聚合查询组装的结果。`from_attributes=True` 允许从字典或类似 ORM 的对象转换。

前端典型展示：

```
┌──────────────────────────────────────┐
│  Bob                     5条未读     │  ← user.nickname, unread_count
│  最后一条消息的预览文本...           │  ← last_message
│  2分钟前                            │  ← updated_at
└──────────────────────────────────────┘
```

### `MarkReadResponse` — 标记已读响应

```python
class MarkReadResponse(BaseModel):
    marked_count: int
    message: str
```

| 字段 | 说明 |
|------|------|
| `marked_count` | 被标记为已读的消息数量 |
| `message` | 操作结果描述，如 `"已将 5 条消息标记为已读"` |

---

## 函数汇总

| 函数/方法 | 所属类 | 装饰器 | 说明 |
|-----------|--------|--------|------|
| `check_not_self(self)` | `MessageCreate` | `@model_validator(mode="after")` | 校验发送者和接收者不能是同一个人 |
| `model_validate()` | `MessageResponse` | 继承 | 从 ORM 对象构建消息响应 |
| `model_validate()` | `ConversationItem` | 继承 | 从聚合查询结果构建会话项 |
