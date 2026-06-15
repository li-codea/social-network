# ORM 模型：User 表

> **源码文件**：`backend/app/models/user.py`

---

## 文件职责

定义用户表的 SQLAlchemy ORM 模型，将 Python 类映射为 MySQL 的 `users` 表。包含用户的身份信息、个人资料、兴趣标签和时间戳。

---

## 导入依赖

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
from app.database import Base
```

| 导入项 | 用途 |
|--------|------|
| `Column` | 定义表列 |
| `Integer` | 整数列类型 |
| `String` | 变长字符串列类型 |
| `Text` | 长文本列类型 |
| `DateTime` | 日期时间列类型 |
| `Index` | 在 `__table_args__` 中创建索引 |
| `JSON` | MySQL 原生 JSON 列类型（`sqlalchemy.types.JSON`） |
| `func` | SQL 函数（`func.now()` 用于服务器端默认时间戳） |
| `Base` | ORM 基类，从 `app.database` 导入 |

---

## 类：`User(Base)`

### 表名

```python
__tablename__ = "users"
```

映射到 MySQL 中的 `users` 表。

### 列定义

#### `id` — 用户主键

```python
id = Column(
    Integer, primary_key=True, autoincrement=True,
    comment="用户主键ID"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| 类型 | `Integer` | 32 位整数 |
| `primary_key` | `True` | 主键 |
| `autoincrement` | `True` | 自增（MySQL AUTO_INCREMENT） |

#### `username` — 唯一用户名

```python
username = Column(
    String(50), unique=True, nullable=False, index=True,
    comment="唯一用户名，用于登录"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| 类型 | `String(50)` | 最长 50 字符 |
| `unique` | `True` | 唯一约束，数据库层面保证不重复 |
| `nullable` | `False` | 不允许 NULL |
| `index` | `True` | 创建单列索引，加速按用户名查询 |

#### `nickname` — 显示昵称

```python
nickname = Column(
    String(100), default=None,
    comment="显示昵称，支持按昵称搜索"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| 类型 | `String(100)` | 最长 100 字符 |
| `default` | `None` | 默认为 NULL |

#### `avatar_url` — 头像 URL

```python
avatar_url = Column(
    String(500), default=None,
    comment="头像图片URL"
)
```

存储用户头像的网络地址，最长 500 字符。

#### `bio` — 个人简介

```python
bio = Column(
    Text, default=None,
    comment="个人简介"
)
```

使用 `Text` 类型（MySQL TEXT），可以存储较长的自我介绍文本。

#### `tags` — 兴趣标签 JSON 数组

```python
tags = Column(
    JSON, default=list,
    comment="兴趣标签 JSON 数组"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| 类型 | `JSON` | MySQL 原生 JSON 列，支持 JSON_OVERLAPS 等函数 |
| `default` | `list` | 默认为空列表 `[]` |

**存储示例**：`["Python", "机器学习", "摄影", "篮球"]`

这是推荐算法的核心字段，通过 `JSON_OVERLAPS` 函数查找兴趣相投的用户。

#### `created_at` — 注册时间

```python
created_at = Column(
    DateTime, server_default=func.now(),
    comment="注册时间"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `server_default` | `func.now()` | 使用 MySQL 服务端的 `NOW()` 函数作为默认值 |

#### `updated_at` — 最后更新时间

```python
updated_at = Column(
    DateTime, server_default=func.now(), onupdate=func.now(),
    comment="最后更新时间"
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `server_default` | `func.now()` | 插入时的默认值 |
| `onupdate` | `func.now()` | 每次更新行时自动刷新时间戳 |

### 表级约束和索引

```python
__table_args__ = (
    Index("idx_users_nickname", "nickname"),
    Index("idx_users_created_at", "created_at"),
    {"comment": "用户表"},
)
```

| 索引名 | 列 | 用途 |
|--------|-----|------|
| `idx_users_nickname` | `nickname` | 加速按昵称搜索（LIKE 查询） |
| `idx_users_created_at` | `created_at` | 加速按注册时间排序（ORDER BY created_at DESC） |

另外，`username` 列上的单列索引在列定义中通过 `index=True` 创建。

### `__repr__`

```python
def __repr__(self):
    return f"<User(id={self.id}, username='{self.username}', nickname='{self.nickname}')>"
```

| 属性 | 说明 |
|------|------|
| **类型** | 实例方法（每个 User 对象都可以调用） |
| **用途** | 定义对象的字符串表示，调试时在日志和控制台中可读地输出用户信息 |

输出示例：`<User(id=1, username='alice', nickname='Alice')>`

---

## 函数汇总

| 函数 | 类型 | 说明 |
|------|------|------|
| `User.__init__()` | 构造函数（继承自 Base） | 创建用户实例，接受关键字参数对应各列 |
| `User.__repr__()` | 实例方法 | 返回人类可读的字符串表示，用于调试输出 |
