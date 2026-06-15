# 路由层：好友关系 API 端点

> **源码文件**：`backend/app/routers/friendships.py`

---

## 文件职责

定义好友关系相关的 RESTful API 端点。所有端点位于 `/api/v1/friendships` 路径前缀下。

---

## 导入依赖

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.friendship import (
    FriendshipCreate, FriendshipResponse, FriendshipExistsResponse,
)
from app.schemas.common import MessageResponse
from app.services import friendship_service
```

---

## 端点列表

| 方法 | 路径 | 函数 | 说明 |
|------|------|------|------|
| POST | `/api/v1/friendships/` | `add_friendship` | 建立好友关系 |
| DELETE | `/api/v1/friendships/{friendship_id}` | `remove_friendship_by_id` | 按记录 ID 解除好友 |
| DELETE | `/api/v1/friendships/users` | `remove_friendship_by_users` | 按用户 ID 对解除好友 |
| GET | `/api/v1/friendships/exists` | `check_friendship` | 检查是否为好友 |

---

## 函数详解

### `add_friendship(data, db)` — POST `/friendships/`

```python
@router.post("/", response_model=FriendshipResponse, status_code=201, summary="添加好友关系")
def add_friendship(data: FriendshipCreate, db: Session = Depends(get_db)):
    try:
        friendship = friendship_service.create_friendship(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return friendship
```

| 属性 | 值 | 说明 |
|------|-----|------|
| 状态码 | `201` | Created |
| 异常处理 | `ValueError → 400` | 用户不存在、已是好友等情况返回 400 Bad Request |

**设计细节**：`FriendshipCreate` 的 `normalize_ids` 已在 Schema 层自动处理 ID 规范化，路由层无需关心传入的 ID 大小。

### `remove_friendship_by_users(user_id, friend_id, db)` — DELETE `/friendships/users`

```python
@router.delete("/users", response_model=MessageResponse, summary="根据用户ID解除好友关系")
def remove_friendship_by_users(
    user_id: int = Query(gt=0, description="用户ID"),
    friend_id: int = Query(gt=0, description="好友ID"),
    db: Session = Depends(get_db),
):
```

| 参数 | 来源 | 校验 |
|------|------|------|
| `user_id` | Query 字符串 | `gt=0` |
| `friend_id` | Query 字符串 | `gt=0` |

**前置校验**：

```
user_id == friend_id?  → 400 "不能对自身执行此操作"
关系不存在？           → 404 "未找到该好友关系"
```

> **路径设计说明**：`DELETE /friendships/users?user_id=1&friend_id=2` 而非 `DELETE /friendships/1/2`。使用 Query 参数是因为两个用户 ID 是平级的，不存在"谁从属于谁"的关系。

### `remove_friendship_by_id(friendship_id, db)` — DELETE `/{friendship_id}`

```python
@router.delete("/{friendship_id}", response_model=MessageResponse, summary="根据关系ID解除好友")
def remove_friendship_by_id(friendship_id: int, db: Session = Depends(get_db)):
    success = friendship_service.delete_friendship(db, friendship_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"好友关系ID {friendship_id} 不存在")
    return MessageResponse(message=f"好友关系 {friendship_id} 已解除")
```

提供两种删除方式是为了灵活性：
- **知道关系 ID**：用 `/{friendship_id}`
- **只知道两个用户 ID**：用 `/users?user_id=&friend_id=`

### `check_friendship(user_id, other_id, db)` — GET `/friendships/exists`

```python
@router.get("/exists", response_model=FriendshipExistsResponse, summary="检查好友关系是否存在")
def check_friendship(
    user_id: int = Query(gt=0, description="用户ID"),
    other_id: int = Query(gt=0, description="另一用户ID"),
    db: Session = Depends(get_db),
):
    are_friends, friendship_id = friendship_service.check_friendship_exists(
        db, user_id, other_id
    )
    return FriendshipExistsResponse(are_friends=are_friends, friendship_id=friendship_id)
```

| 参数 | 说明 |
|------|------|
| `other_id` | 使用 `other_id` 而非 `friend_id`，因为此时还不知道是否是好友 |

这个端点常用于：在用户 A 的主页上判断"我与 A 是否已经是好友"，以决定显示"添加好友"按钮还是"发消息"按钮。

---

## 函数汇总

| 函数 | HTTP 方法 | 路径 | 状态码 | response_model |
|------|-----------|------|--------|----------------|
| `add_friendship()` | POST | `/` | 201 | `FriendshipResponse` |
| `remove_friendship_by_users()` | DELETE | `/users` | 200 | `MessageResponse` |
| `remove_friendship_by_id()` | DELETE | `/{friendship_id}` | 200 | `MessageResponse` |
| `check_friendship()` | GET | `/exists` | 200 | `FriendshipExistsResponse` |
