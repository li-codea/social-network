# 服务层：聊天业务逻辑

> **源码文件**：`backend/app/services/chat_service.py`

---

## 文件职责

封装私聊消息的核心业务逻辑：发送消息、获取会话列表（聚合查询）、获取聊天记录（分页）、批量标记消息已读。

---

## 导入依赖

```python
from typing import Optional
from sqlalchemy import func, or_, and_, case, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.models.message import Message
from app.models.user import User
from app.utils.pagination import get_pagination_slice
```

---

## 函数详解

### `send_message(db, sender_id, receiver_id, content)` — 发送消息

```python
def send_message(
    db: Session, sender_id: int, receiver_id: int, content: str
) -> Message:
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `sender_id` | `int` | 发送者用户 ID |
| `receiver_id` | `int` | 接收者用户 ID |
| `content` | `str` | 消息文本（已在 Schema 层校验 1~5000 字符） |

**三重校验**：

```
sender_id == receiver_id? → ValueError("不能给自己发送消息")
发送者存在？              → ValueError("发送者用户ID X 不存在")
接收者存在？              → ValueError("接收者用户ID X 不存在")
```

校验通过后，创建 `Message` ORM 对象、`commit()`、`refresh()` 返回。

### `get_conversations(db, user_id, page, page_size)` — 获取会话列表

这是本文件中最复杂的函数，使用原始 SQL 进行聚合查询。

**核心 SQL（第一步：聚合统计）**：

```sql
SELECT
    CASE
        WHEN m.sender_id = :uid THEN m.receiver_id
        ELSE m.sender_id
    END AS other_id,
    MAX(m.created_at) AS updated_at,
    SUM(CASE WHEN m.receiver_id = :uid AND m.is_read = 0 THEN 1 ELSE 0 END) AS unread_count
FROM messages m
WHERE m.sender_id = :uid OR m.receiver_id = :uid
GROUP BY other_id
ORDER BY updated_at DESC
```

| SQL 技术 | 说明 |
|----------|------|
| `CASE WHEN sender_id = :uid THEN receiver_id ELSE sender_id END` | 确定"对方用户"的 ID——如果当前用户是发送者，对方就是接收者；反之亦然 |
| `MAX(m.created_at)` | 每个会话的最后消息时间 |
| `SUM(CASE WHEN ... is_read = 0 THEN 1 ELSE 0 END)` | **带条件聚合**：只计算接收者是当前用户且未读的消息 |
| `WHERE sender_id = :uid OR receiver_id = :uid` | 筛选涉及当前用户的所有消息 |
| `GROUP BY other_id` | 按对方用户分组，生成每个会话的聚合统计 |
| `ORDER BY updated_at DESC` | 最近活跃的会话排在最前面 |

**第二步：分页**

```python
total = len(all_rows)
offset, limit = get_pagination_slice(page, page_size)
page_rows = all_rows[offset:offset + limit]
```

由于聚合查询结果集通常不大（用户通常只有几十个会话），这里采用 Python 列表切片分页，而非 SQL LIMIT/OFFSET。

**第三步：批量加载详情**

```python
# 批量加载对方用户信息
other_ids = [row.other_id for row in page_rows]
users_map = {u.id: u for u in db.query(User).filter(User.id.in_(other_ids)).all()}

# 批量获取每个会话的最后一条消息内容
last_msg_sql = text("""
    SELECT m.content
    FROM messages m
    WHERE ((m.sender_id = :uid AND m.receiver_id = :oid)
        OR (m.sender_id = :oid AND m.receiver_id = :uid))
    ORDER BY m.created_at DESC
    LIMIT 1
""")
```

| 步骤 | 说明 |
|------|------|
| 批量加载用户 | 一次 `IN` 查询加载所有对方用户的 `User` 对象，避免 N+1 查询 |
| 逐条获取最后消息 | 对每个会话查询最近一条消息的内容（每条一个 LIMIT 1 查询） |

**第四步：组装返回**

```python
conversations.append({
    "user": UserBrief.model_validate(other_user),
    "last_message": last_message,
    "unread_count": row.unread_count,
    "updated_at": row.updated_at,
})
```

### `get_chat_history(db, user_id, other_id, page, page_size)` — 获取聊天记录

```python
def get_chat_history(
    db: Session, user_id: int, other_id: int,
    page: int = 1, page_size: int = 50,
) -> tuple[list[Message], int]:
```

**查询逻辑**：

```python
query = db.query(Message).filter(
    or_(
        and_(Message.sender_id == user_id, Message.receiver_id == other_id),
        and_(Message.sender_id == other_id, Message.receiver_id == user_id),
    )
)
```

| 条件 | 含义 | SQL 等价 |
|------|------|----------|
| `and_(A→B)` | 用户发给对方 | `sender_id = X AND receiver_id = Y` |
| `and_(B→A)` | 对方发给用户 | `sender_id = Y AND receiver_id = X` |
| `or_(..., ...)` | 任一方向的通信 | `(X→Y) OR (Y→X)` |

结果按 `created_at DESC` 排序（最新消息在前），使用 `offset/limit` 分页。

### `mark_as_read(db, user_id, other_id)` — 标记已读

```python
def mark_as_read(db: Session, user_id: int, other_id: int) -> int:
    count = (
        db.query(Message)
        .filter(
            Message.sender_id == other_id,   # 对方发送的
            Message.receiver_id == user_id,  # 当前用户收到的
            Message.is_read == False,         # 未读的
        )
        .count()
    )

    if count > 0:
        db.query(Message).filter(
            Message.sender_id == other_id,
            Message.receiver_id == user_id,
            Message.is_read == False,
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()

    return count
```

| 步骤 | 说明 |
|------|------|
| 1. 计数 | 先统计符合条件的未读消息数（用于返回值） |
| 2. 批量更新 | 使用 `update()` 一次性将所有符合条件的消息标记为已读，避免逐条更新（N+1 问题） |
| 3. `synchronize_session=False` | 告诉 SQLAlchemy 不将会话中已有的对象与 UPDATE 结果同步（性能优化） |

**关键细节**：`is_read` 只标记**对方发给当前用户**的消息（`sender_id == other_id, receiver_id == user_id`），不会标记反方向的消息。

---

## 函数汇总

| 函数 | 参数 | 返回 | 可能异常 |
|------|------|------|----------|
| `send_message()` | `db, sender_id, receiver_id, content` | `Message` ORM 对象 | `ValueError`：自己发给自己、用户不存在 |
| `get_conversations()` | `db, user_id, page, page_size` | `(list[dict], int)` | `ValueError`：用户不存在 |
| `get_chat_history()` | `db, user_id, other_id, page, page_size` | `(list[Message], int)` | `ValueError`：自己与自己聊天 |
| `mark_as_read()` | `db, user_id, other_id` | `int`（标记数） | 无 |
