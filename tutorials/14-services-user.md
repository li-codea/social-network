# 服务层：用户业务逻辑

> **源码文件**：`backend/app/services/user_service.py`

---

## 文件职责

封装用户相关的业务逻辑：创建、查询（按 ID / 分页搜索）、更新（部分更新）、删除（级联删除好友关系）。所有函数以 `db` 会话作为第一个参数，不直接处理 HTTP 异常。

---

## 导入依赖

```python
from typing import Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.friendship import Friendship
from app.schemas.user import UserCreate, UserUpdate
from app.utils.pagination import get_pagination_slice
```

---

## 函数详解

### `create_user(db, data)` — 创建新用户

```python
def create_user(db: Session, data: UserCreate) -> User:
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise ValueError(f"用户名 '{data.username}' 已被占用")

    user = User(
        username=data.username,
        nickname=data.nickname,
        avatar_url=data.avatar_url,
        bio=data.bio,
        tags=data.tags or [],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `db` | `Session` | 数据库会话（FastAPI 注入） |
| `data` | `UserCreate` | 经过 Pydantic 校验的创建数据 |
| **返回** | `User` | 新创建的 ORM 对象 |
| **异常** | `ValueError` | 用户名已被占用 |

**执行流程**：

1. **唯一性检查**：查询 `username` 是否已存在，存在则抛出 `ValueError`
2. **创建 ORM 对象**：将 Pydantic 字段映射到 ORM 字段。`data.tags or []` 确保 tags 永远不是 None
3. `db.add(user)` — 将对象加入会话的待插入队列
4. `db.commit()` — 执行 SQL INSERT，写入数据库
5. `db.refresh(user)` — 从数据库重新加载对象，获取自增 ID 和数据库默认值（如 `created_at`）

### `get_user_by_id(db, user_id)` — 按 ID 查询

```python
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
```

| 参数 | 说明 |
|------|------|
| **返回** | 找到返回 `User` 对象，不存在返回 `None` |

使用 `.first()` 而非 `.one()` — 不存时不抛异常，返回 `None`，由调用方决定如何处理。

### `get_users_paginated(db, page, page_size, keyword)` — 分页搜索

```python
def get_users_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
) -> tuple[list[User], int]:
    query = db.query(User)
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                User.nickname.like(like_pattern),
                User.username.like(like_pattern),
            )
        )

    total = query.count()
    offset, limit = get_pagination_slice(page, page_size)
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return users, total
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | `Optional[str]` | `None` | 搜索关键词，模糊匹配昵称或用户名 |

**搜索逻辑**：

```sql
-- 当 keyword = "alice" 时生成的 SQL（近似）：
SELECT * FROM users
WHERE nickname LIKE '%alice%' OR username LIKE '%alice%'
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

- 使用 `or_()` 组合两个 LIKE 条件，匹配任一字段即可
- `%keyword%` 模糊匹配（前后都可以有任意字符）
- 按注册时间倒序，最新的用户排在前面

**返回值**：`(列表, 总数)` 二元组 —— 列表是当前页的数据，总数用于前端分页器显示总页数。

### `update_user(db, user_id, data)` — 部分更新用户

```python
def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
```

| 关键方法 | 说明 |
|----------|------|
| `data.model_dump(exclude_unset=True)` | 将 Pydantic 模型转为字典，但**只包含被显式设置的字段** |

**部分更新示例**：

```python
# 请求只传了 bio
PUT /users/1  {"bio": "I love coding"}

# model_dump(exclude_unset=True) 只返回：
{"bio": "I love coding"}
# username 和 tags 不会被覆盖为 None
```

| 步骤 | 说明 |
|------|------|
| 1. 查询用户 | 不存在则返回 `None` |
| 2. `model_dump(exclude_unset=True)` | 提取只被显式设置的非 None 字段 |
| 3. `setattr(user, field, value)` | 动态设置 ORM 对象的属性 |
| 4. `commit()` + `refresh()` | 更新数据库并重新加载 |

### `delete_user(db, user_id)` — 删除用户（级联）

```python
def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    db.query(Friendship).filter(
        (Friendship.user_id == user_id) | (Friendship.friend_id == user_id)
    ).delete()

    db.delete(user)
    db.commit()
    return True
```

| 步骤 | 说明 |
|------|------|
| 1. 查找用户 | 不存在返回 `False` |
| 2. 级联删除好友关系 | 删除该用户参与的所有好友关系记录。使用 `\|` (OR) 运算符从 `user_id` 和 `friend_id` 两列匹配 |
| 3. 删除用户本身 | `db.delete(user)` |
| 4. 提交事务 | `db.commit()` |

对应的 SQL：

```sql
-- 1. 删除好友关系
DELETE FROM friendships WHERE user_id = 3 OR friend_id = 3;

-- 2. 删除用户
DELETE FROM users WHERE id = 3;
```

---

## 函数汇总

| 函数 | 参数 | 返回 | 可能异常 |
|------|------|------|----------|
| `create_user()` | `db, data` | `User` ORM 对象 | `ValueError`：用户名已存在 |
| `get_user_by_id()` | `db, user_id` | `User` 或 `None` | 无 |
| `get_users_paginated()` | `db, page, page_size, keyword` | `(list[User], int)` | 无 |
| `update_user()` | `db, user_id, data` | `User` 或 `None` | 无 |
| `delete_user()` | `db, user_id` | `bool`（成功/失败） | 无 |
