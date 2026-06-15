# 路由层：用户 API 端点

> **源码文件**：`backend/app/routers/users.py`

---

## 文件职责

定义用户相关的 RESTful API 端点，负责接收 HTTP 请求、校验参数、调用服务层、返回响应。所有端点位于 `/api/v1/users` 路径前缀下。

---

## 导入依赖

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserBrief
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services import user_service, friendship_service, recommendation_service
```

---

## 端点列表

| 方法 | 路径 | 函数 | 说明 |
|------|------|------|------|
| POST | `/api/v1/users/` | `create_user` | 创建新用户 |
| GET | `/api/v1/users/` | `list_users` | 分页获取用户列表（支持搜索） |
| GET | `/api/v1/users/{user_id}` | `get_user` | 获取用户详情 |
| PUT | `/api/v1/users/{user_id}` | `update_user` | 更新用户信息 |
| DELETE | `/api/v1/users/{user_id}` | `delete_user` | 删除用户 |
| GET | `/api/v1/users/{user_id}/friends` | `get_user_friends` | 获取好友列表 |
| GET | `/api/v1/users/{user_id}/common-friends/{other_id}` | `get_common_friends` | 获取共同好友 |
| GET | `/api/v1/users/{user_id}/recommendations` | `get_recommendations` | 获取好友推荐 |

---

## 函数详解

### `create_user(data, db)` — POST `/users/`

```python
@router.post("/", response_model=UserResponse, status_code=201, summary="创建用户")
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = user_service.create_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return user
```

| 属性 | 值 | 说明 |
|------|-----|------|
| 状态码 | `201` | Created — 资源创建成功 |
| `response_model` | `UserResponse` | 自动将返回的 ORM 对象序列化为 JSON |
| 异常处理 | `ValueError → 409` | 用户名冲突返回 409 Conflict |

### `list_users(page, page_size, keyword, db)` — GET `/users/`

```python
@router.get("/", response_model=PaginatedResponse[UserResponse], summary="获取用户列表")
def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    keyword: str = Query(default="", description="按昵称或用户名搜索"),
    db: Session = Depends(get_db),
):
```

| 参数 | 来源 | 说明 |
|------|------|------|
| `page` | Query 字符串 | 页码，默认 1 |
| `page_size` | Query 字符串 | 每页数量，默认 20，最大 100 |
| `keyword` | Query 字符串 | 搜索关键词，默认空字符串 |

**响应示例**：

```json
{
    "items": [...],
    "total": 50,
    "page": 1,
    "page_size": 20
}
```

### `get_user(user_id, db)` — GET `/users/{user_id}`

```python
@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return user
```

用户不存在返回 `404 Not Found`。

### `update_user(user_id, data, db)` — PUT `/users/{user_id}`

```python
@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = user_service.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return user
```

支持部分更新：只更新请求中传入的非空字段。用户不存在返回 404。

### `delete_user(user_id, db)` — DELETE `/users/{user_id}`

```python
@router.delete("/{user_id}", response_model=MessageResponse, summary="删除用户")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return MessageResponse(message=f"用户 {user_id} 已删除")
```

删除操作不返回实体数据，使用 `MessageResponse`（成功消息）。

### `get_user_friends(user_id, page, page_size, db)` — GET `/{user_id}/friends`

```python
@router.get(
    "/{user_id}/friends",
    response_model=PaginatedResponse[UserBrief],
    summary="获取用户好友列表",
)
def get_user_friends(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
```

| 细节 | 说明 |
|------|------|
| `response_model` | `PaginatedResponse[UserBrief]` — 好友列表使用简要用户信息 |
| 前置校验 | 先检查用户是否存在，不存在返回 404 |

### `get_common_friends(user_id, other_id, db)` — GET `/{user_id}/common-friends/{other_id}`

```python
@router.get(
    "/{user_id}/common-friends/{other_id}",
    summary="获取两个用户的共同好友",
)
def get_common_friends(user_id: int, other_id: int, db: Session = Depends(get_db)):
```

**三步前置校验**：

```
user_id == other_id?       → 400 "不能与自身比较"
用户 A 不存在？             → 404
用户 B 不存在？             → 404
```

**返回结构**（非标准分页响应）：

```json
{
    "user_a": { ... },
    "user_b": { ... },
    "common_friends": [ ... ],
    "count": 3
}
```

### `get_recommendations(user_id, page, page_size, max_degree, db)` — GET `/{user_id}/recommendations`

```python
@router.get("/{user_id}/recommendations", summary="获取好友推荐列表")
def get_recommendations(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    max_degree: int = Query(default=3, ge=2, le=3, description="最大好友度数(2或3)"),
    db: Session = Depends(get_db),
):
```

| 参数 | 校验 | 说明 |
|------|------|------|
| `max_degree` | `ge=2, le=3` | 只允许 2（只推荐二度好友）或 3（推荐二度+三度好友） |

推荐结果中每条包含：

```json
{
    "user": { "id": 5, "username": "eve", ... },
    "score": 9,
    "reason": {
        "common_friends_count": 2,
        "common_friends": [{ ... }, { ... }],
        "common_tags_count": 1,
        "common_tags": ["Python"],
        "degree": 2
    }
}
```

---

## 函数汇总

| 函数 | HTTP 方法 | 路径 | 状态码 | response_model |
|------|-----------|------|--------|----------------|
| `create_user()` | POST | `/` | 201 | `UserResponse` |
| `list_users()` | GET | `/` | 200 | `PaginatedResponse[UserResponse]` |
| `get_user()` | GET | `/{user_id}` | 200 | `UserResponse` |
| `update_user()` | PUT | `/{user_id}` | 200 | `UserResponse` |
| `delete_user()` | DELETE | `/{user_id}` | 200 | `MessageResponse` |
| `get_user_friends()` | GET | `/{user_id}/friends` | 200 | `PaginatedResponse[UserBrief]` |
| `get_common_friends()` | GET | `/{user_id}/common-friends/{other_id}` | 200 | 自定义字典 |
| `get_recommendations()` | GET | `/{user_id}/recommendations` | 200 | `PaginatedResponse` |
