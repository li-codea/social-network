# Routers 包初始化

> **源码文件**：`backend/app/routers/__init__.py`

---

## 文件职责

将 `routers` 子包中的三个路由模块统一导出，使 `main.py` 可以通过 `from app.routers import users, friendships, chat` 简洁导入。

---

## 代码

```python
from app.routers import users, friendships, chat

__all__ = ["users", "friendships", "chat"]
```

---

## 导出的模块

| 变量名 | 对应文件 | 路由前缀 | 主要功能 |
|--------|---------|----------|---------|
| `users` | `routers/users.py` | `/users` | 用户 CRUD + 好友列表 + 共同好友 + 推荐 |
| `friendships` | `routers/friendships.py` | `/friendships` | 好友关系增删查 |
| `chat` | `routers/chat.py` | `/messages` | 消息发送 + 会话列表 + 聊天记录 + 已读标记 |

> **注意**：路由模块导出的是模块对象，`main.py` 中使用 `app.include_router(users.router)` 注册的是模块内部的 `router` 实例。

---

## 函数汇总

| 变量 | 说明 |
|------|------|
| `__all__` | 控制通配符导入时导出的 3 个路由模块名 |
