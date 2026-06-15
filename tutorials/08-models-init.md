# Models 包初始化

> **源码文件**：`backend/app/models/__init__.py`

---

## 文件职责

将 `models` 子包中的三个 ORM 模型类 (`User`, `Friendship`, `Message`) 统一导出，使其他模块可以通过简洁的 `from app.models import User` 方式导入。

---

## 代码

```python
from app.models.user import User
from app.models.friendship import Friendship
from app.models.message import Message

__all__ = ["User", "Friendship", "Message"]
```

---

## 函数/变量详解

### 模块导入

| 导入语句 | 说明 |
|----------|------|
| `from app.models.user import User` | 导入用户 ORM 模型类 |
| `from app.models.friendship import Friendship` | 导入好友关系 ORM 模型类 |
| `from app.models.message import Message` | 导入消息 ORM 模型类 |

### `__all__` 列表

```python
__all__ = ["User", "Friendship", "Message"]
```

| 变量 | 类型 | 说明 |
|------|------|------|
| `__all__` | `list[str]` | 控制 `from app.models import *` 时导出的符号。只导出三个核心 ORM 类，不暴露内部模块 |

---

## 使用效果

有 `__init__.py` 后，其他模块可以这样导入：

```python
# 简洁写法（推荐）
from app.models import User, Friendship, Message

# 等价于全路径写法
from app.models.user import User
from app.models.friendship import Friendship
from app.models.message import Message
```

---

## 函数汇总

| 函数/变量 | 类型 | 说明 |
|-----------|------|------|
| `__all__` | 模块变量 | 控制通配符导入时导出的符号列表 |
