# Schema：好友关系数据模型

> **源码文件**：`backend/app/schemas/friendship.py`

---

## 文件职责

定义好友关系相关的 Pydantic 数据模型。核心功能是在 `FriendshipCreate` 中使用 `model_validator` 自动规范化用户 ID 顺序，确保调用方无需关心传入的 ID 大小关系。

---

## 导入依赖

```python
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
```

| 导入项 | 用途 |
|--------|------|
| `datetime` | 类型注解中表示创建时间 |
| `model_validator` | Pydantic v2 模型级校验器（校验整个模型而不仅仅是单个字段） |

---

## 类详解

### `FriendshipCreate` — 创建好友关系请求体

```python
class FriendshipCreate(BaseModel):
    user_id: int = Field(gt=0, description="用户ID")
    friend_id: int = Field(gt=0, description="好友ID")
```

| 字段 | 校验 | 说明 |
|------|------|------|
| `user_id` | `gt=0`（大于 0） | 任意一个用户的 ID |
| `friend_id` | `gt=0`（大于 0） | 另一个用户的 ID |

#### `normalize_ids(self)` — 规范化 ID 顺序

```python
@model_validator(mode="after")
def normalize_ids(self) -> "FriendshipCreate":
    if self.user_id == self.friend_id:
        raise ValueError("不能添加自己为好友")
    if self.user_id > self.friend_id:
        self.user_id, self.friend_id = self.friend_id, self.user_id
    return self
```

| 属性 | 说明 |
|------|------|
| **装饰器** | `@model_validator(mode="after")` — 在所有字段校验完成后执行 |
| **触发时机** | 字段级校验器（如 `gt=0`）之后、模型构造完成之前 |
| **返回值** | 修改后的 `self`（Pydantic v2 要求返回模型实例） |

**执行逻辑**：

```
输入: user_id=5, friend_id=3
  ↓
字段校验: 5 > 0 ✓, 3 > 0 ✓
  ↓
normalize_ids():
  1. 5 == 3? No ✓（不是自己加自己）
  2. 5 > 3? Yes → 交换: user_id=3, friend_id=5
  ↓
输出: user_id=3, friend_id=5  (始终 user_id < friend_id)
```

**设计意义**：

- **调用方友好**：前端不需要关心 ID 大小顺序，直接传两个用户 ID 即可
- **数据库一致**：在到达数据库之前就规范化为 `user_id < friend_id`，与 `Friendship` ORM 模型的 CHECK 约束对齐
- **校验前置**：在 Pydantic 层就阻止"添加自己为好友"的操作，无需进入业务层

### `FriendshipResponse` — 好友关系响应

```python
class FriendshipResponse(BaseModel):
    id: int
    user_id: int
    friend_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

| 字段 | 说明 |
|------|------|
| `id` | 好友关系记录的主键 |
| `user_id` | 较小的用户 ID |
| `friend_id` | 较大的用户 ID |
| `created_at` | 关系建立时间 |

`from_attributes=True` 允许直接从 SQLAlchemy `Friendship` ORM 对象转换。

### `FriendshipExistsResponse` — 好友关系存在性检查响应

```python
class FriendshipExistsResponse(BaseModel):
    are_friends: bool = Field(description="两人是否为好友")
    friendship_id: int | None = Field(default=None, description="若为好友，返回关系记录ID")
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `are_friends` | `bool` | `True` = 是好友，`False` = 不是好友 |
| `friendship_id` | `int \| None` | 是好友时返回关系记录 ID；不是好友时为 `None` |

使用的类型注解 `int | None` 是 Python 3.10+ 的联合类型语法，等价于 `Optional[int]`。

**响应示例**：

```json
// 是好友
{"are_friends": true, "friendship_id": 3}

// 不是好友
{"are_friends": false, "friendship_id": null}
```

---

## 函数汇总

| 函数/方法 | 所属类 | 装饰器 | 说明 |
|-----------|--------|--------|------|
| `normalize_ids(self)` | `FriendshipCreate` | `@model_validator(mode="after")` | 校验不自己加自己；若 user_id > friend_id 则交换两者，确保 user_id < friend_id |
| `model_validate()` | `FriendshipResponse` | 继承 | 从 ORM 对象构建响应 |
