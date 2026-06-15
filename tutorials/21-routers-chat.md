# 路由层：聊天 API 端点

> **源码文件**：`backend/app/routers/chat.py`

---

## 文件职责

定义私聊消息相关的 RESTful API 端点。所有端点位于 `/api/v1/messages` 路径前缀下。

---

## 导入依赖

```python
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.message import (
    MessageCreate, MessageResponse, ConversationItem, MarkReadResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import chat_service
```

---

## 端点列表

| 方法 | 路径 | 函数 | 说明 |
|------|------|------|------|
| POST | `/api/v1/messages/` | `send_message` | 发送消息 |
| GET | `/api/v1/messages/conversations` | `list_conversations` | 获取会话列表 |
| GET | `/api/v1/messages/` | `get_messages` | 获取聊天记录 |
| PUT | `/api/v1/messages/read` | `mark_read` | 标记消息已读 |

---

## 函数详解

### `send_message(data, db)` — POST `/messages/`

```python
@router.post("/", response_model=MessageResponse, status_code=201, summary="发送消息")
def send_message(data: MessageCreate, db: Session = Depends(get_db)):
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
```

| 属性 | 值 | 说明 |
|------|-----|------|
| 状态码 | `201` | Created |
| 异常处理 | `ValueError → 400` | 用户不存在或自己发给自己 |

### `list_conversations(user_id, page, page_size, db)` — GET `/messages/conversations`

```python
@router.get(
    "/conversations",
    response_model=PaginatedResponse[ConversationItem],
    summary="获取会话列表",
)
def list_conversations(
    user_id: int = Query(gt=0, description="当前用户ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
```

| 参数 | 说明 |
|------|------|
| `user_id` | **必填**，当前登录用户的 ID |
| `page` / `page_size` | 分页参数 |

**异常处理**：用户不存在时，`ValueError` 转换为 `404`。

### `get_messages(user_id, other_id, page, page_size, db)` — GET `/messages/`

```python
@router.get("/", response_model=PaginatedResponse[MessageResponse], summary="获取聊天记录")
def get_messages(
    user_id: int = Query(gt=0, description="当前用户ID"),
    other_id: int = Query(gt=0, description="对方用户ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `user_id` | 必填 | 当前用户 |
| `other_id` | 必填 | 对话对方 |
| `page_size` | `50` | 聊天记录每页默认为 50 条（比用户列表的 20 条更多） |

**异常处理**：`user_id == other_id` 或其它错误 → 400 Bad Request。

### `mark_read(user_id, other_id, db)` — PUT `/messages/read`

```python
@router.put("/read", response_model=MarkReadResponse, summary="标记消息已读")
def mark_read(
    user_id: int = Query(gt=0, description="当前用户ID（接收者）"),
    other_id: int = Query(gt=0, description="对方用户ID（发送者）"),
    db: Session = Depends(get_db),
):
    count = chat_service.mark_as_read(db, user_id=user_id, other_id=other_id)
    return MarkReadResponse(
        marked_count=count,
        message=f"已将 {count} 条消息标记为已读",
    )
```

| 属性 | 说明 |
|------|------|
| HTTP 方法 | `PUT` — 部分更新资源（标记已读不创建新资源） |
| 幂等性 | 多次调用会成功但返回 `marked_count=0`（没有新未读消息时） |

---

## 函数汇总

| 函数 | HTTP 方法 | 路径 | 状态码 | response_model |
|------|-----------|------|--------|----------------|
| `send_message()` | POST | `/` | 201 | `MessageResponse` |
| `list_conversations()` | GET | `/conversations` | 200 | `PaginatedResponse[ConversationItem]` |
| `get_messages()` | GET | `/` | 200 | `PaginatedResponse[MessageResponse]` |
| `mark_read()` | PUT | `/read` | 200 | `MarkReadResponse` |
