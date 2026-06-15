# ORM 模型：Friendship 无向好友关系表

> **源码文件**：`backend/app/models/friendship.py`

---

## 文件职责

定义好友关系表的 ORM 模型。核心设计是**无向边存储**：通过 CHECK 约束强制 `user_id < friend_id`，结合 UNIQUE 约束保证每对用户只有一条关系记录。

---

## 核心设计思想

传统有向关系表：

```
| user_id | friend_id |
|---------|-----------|
| 1       | 2         |
| 2       | 1         |  ← 冗余！
```

本项目的无向关系表：

```
| user_id | friend_id |
|---------|-----------|
| 1       | 2         |  ← 只有一条，user_id 永远 < friend_id
```

**查询用户 X 的所有好友时**，需要从两列同时查询：

```sql
SELECT * FROM friendships WHERE user_id = X OR friend_id = X
```

---

## 导入依赖

```python
from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index,
)
from sqlalchemy.sql import func
from app.database import Base
```

| 导入项 | 用途 |
|--------|------|
| `ForeignKey` | 外键约束，引用 `users.id` |
| `UniqueConstraint` | 复合唯一约束 |
| `CheckConstraint` | CHECK 约束（`user_id < friend_id`） |

---

## 类：`Friendship(Base)`

### 表名

```python
__tablename__ = "friendships"
```

### 列定义

#### `id` — 关系主键

```python
id = Column(
    Integer, primary_key=True, autoincrement=True,
    comment="关系主键ID"
)
```

自增主键，每条好友关系记录的唯一标识。

#### `user_id` — 较小 ID 的用户

```python
user_id = Column(
    Integer, ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    comment="较小ID的用户"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `ForeignKey` | `"users.id"` | 引用 users 表的 id 列 |
| `ondelete` | `"CASCADE"` | 删除用户时，级联删除其所有好友关系 |

#### `friend_id` — 较大 ID 的用户

```python
friend_id = Column(
    Integer, ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    comment="较大ID的用户"
)
```

与 `user_id` 对称，同样有外键 + 级联删除。

#### `created_at` — 关系建立时间

```python
created_at = Column(
    DateTime, server_default=func.now(),
    comment="好友关系建立时间"
)
```

好友关系何时建立。使用 MySQL 服务端 NOW() 作为默认值。

### 表级约束和索引

```python
__table_args__ = (
    UniqueConstraint("user_id", "friend_id", name="uq_friendship_pair"),
    CheckConstraint("user_id < friend_id", name="ck_user_lt_friend"),
    Index("idx_friendship_user_id", "user_id"),
    Index("idx_friendship_friend_id", "friend_id"),
    {"comment": "无向好友关系表，user_id < friend_id 约束保证唯一性"},
)
```

| 约束/索引 | 名称 | 作用 |
|-----------|------|------|
| `UniqueConstraint` | `uq_friendship_pair` | 保证 `(user_id, friend_id)` 组合唯一，防止重复关系 |
| `CheckConstraint` | `ck_user_lt_friend` | 强制 `user_id < friend_id`，确保无向边的规范化存储 |
| `Index` | `idx_friendship_user_id` | 加速按较小用户 ID 查询好友 |
| `Index` | `idx_friendship_friend_id` | 加速按较大用户 ID 查询好友 |

### `__repr__`

```python
def __repr__(self):
    return f"<Friendship(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id})>"
```

输出示例：`<Friendship(id=1, user_id=1, friend_id=2)>`

---

## 函数汇总

| 函数 | 类型 | 说明 |
|------|------|------|
| `Friendship.__init__()` | 构造函数（继承自 Base） | 创建好友关系实例 |
| `Friendship.__repr__()` | 实例方法 | 返回人类可读的字符串表示，用于调试 |
