# Services 包初始化

> **源码文件**：`backend/app/services/__init__.py`

---

## 文件职责

将 `services` 子包中的四个服务模块统一导出，方便路由层通过 `from app.services import user_service` 的方式导入。

---

## 代码

```python
from app.services import user_service, friendship_service, recommendation_service, chat_service

__all__ = ["user_service", "friendship_service", "recommendation_service", "chat_service"]
```

---

## 导出的模块

| 模块 | 变量名 | 包含的功能 |
|------|--------|-----------|
| `user_service` | `user_service` | 用户 CRUD：创建、查询、更新、删除、分页搜索 |
| `friendship_service` | `friendship_service` | 好友关系：添加、删除、存在性检查、好友列表、共同好友 |
| `recommendation_service` | `recommendation_service` | 推荐引擎：CTE 递归、标签匹配、加权评分推荐 |
| `chat_service` | `chat_service` | 聊天功能：发送消息、会话列表、聊天记录、标记已读 |

> **注意**：这里导出的是**模块对象**而非模块中的函数。路由层使用方式为 `user_service.create_user(...)` 而非 `create_user(...)`。这种设计的好处是函数名保持简洁（`create_user` 而非 `user_create_user`），同时通过模块前缀避免命名冲突。

---

## 函数汇总

| 变量 | 说明 |
|------|------|
| `__all__` | 控制通配符导入时导出的 4 个服务模块名 |
