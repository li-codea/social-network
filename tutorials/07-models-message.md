# ORM 模型：Message 私聊消息表

> **源码文件**：`backend/app/models/message.py`

---

## 文件职责

定义私聊消息表的 ORM 模型。存储两个用户之间的所有聊天消息，支持单向发送、已读/未读标记、以及高效的双向会话查询。

---

## 导入依赖

```python
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func, text
from app.database import Base
```

| 导入项 | 用途 |
|--------|------|
| `Boolean` | 布尔列类型（映射到 MySQL TINYINT(1)） |
| `text` | 在 `server_default` 中使用原始 SQL 表达式 |

---

## 类：`Message(Base)`

### 表名

```python
__tablename__ = "messages"
```

### 列定义

#### `id` — 消息主键

```python
id = Column(
    Integer, primary_key=True, autoincrement=True,
    comment="消息主键ID"
)
```

自增主键，每条消息的唯一标识。

#### `sender_id` — 发送者

```python
sender_id = Column(
    Integer,
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    comment="发送者用户ID"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `ForeignKey` | `"users.id"` | 外键引用 users 表 |
| `ondelete` | `"CASCADE"` | 用户被删除时，其发送的消息也会被删除 |

#### `receiver_id` — 接收者

```python
receiver_id = Column(
    Integer,
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    comment="接收者用户ID"
)
```

与 `sender_id` 对称的外键设置。

#### `content` — 消息文本内容

```python
content = Column(
    Text, nullable=False,
    comment="消息文本内容"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| 类型 | `Text` | MySQL TEXT 类型，可存储较长的文本消息 |
| `nullable` | `False` | 不允许空消息 |

#### `is_read` — 已读标记

```python
is_read = Column(
    Boolean, nullable=False,
    server_default=text("0"),
    comment="是否已读（0=未读 1=已读）"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| 类型 | `Boolean` | 映射为 MySQL TINYINT(1) |
| `server_default` | `text("0")` | MySQL 层面的默认值为 0（未读） |
| 值的含义 | `0` = 未读, `1` = 已读 | 用于未读消息计数 |

这里使用 `text("0")` 而非 `False`，因为在 MySQL 中布尔值以 0/1 存储，显式指定可以避免歧义。

#### `created_at` — 消息发送时间

```python
created_at = Column(
    DateTime, server_default=func.now(),
    comment="消息发送时间"
)
```

使用 MySQL 服务端 NOW() 自动记录消息发送时间。

### 表级索引

```python
__table_args__ = (
    Index("idx_messages_sender_id", "sender_id"),
    Index("idx_messages_receiver_id", "receiver_id"),
    Index("idx_messages_pair", "sender_id", "receiver_id"),
    Index("idx_messages_created_at", "created_at"),
    {"comment": "私聊消息表"},
)
```

| 索引 | 列 | 用途 |
|------|-----|------|
| `idx_messages_sender_id` | `sender_id` | 加速查询某用户发送的所有消息 |
| `idx_messages_receiver_id` | `receiver_id` | 加速查询某用户收到的所有消息 |
| `idx_messages_pair` | `(sender_id, receiver_id)` | **复合索引**，加速两人之间的会话查询 |
| `idx_messages_created_at` | `created_at` | 加速按时间排序和范围查询 |

`idx_messages_pair` 复合索引的设计尤为关键——查询聊天记录时最常见的 WHERE 条件是 `(sender_id = X AND receiver_id = Y) OR (sender_id = Y AND receiver_id = X)`，复合索引能够高效覆盖这两种情况。

### `__repr__`

```python
def __repr__(self):
    return (
        f"<Message(id={self.id}, sender={self.sender_id}, "
        f"receiver={self.receiver_id}, read={self.is_read})>"
    )
```

输出示例：`<Message(id=42, sender=1, receiver=2, read=False)>`

---

## 函数汇总

| 函数 | 类型 | 说明 |
|------|------|------|
| `Message.__init__()` | 构造函数（继承自 Base） | 创建消息实例 |
| `Message.__repr__()` | 实例方法 | 返回人类可读的字符串表示 |
