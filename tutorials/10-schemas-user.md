# Schema：用户数据模型

> **源码文件**：`backend/app/schemas/user.py`

---

## 文件职责

定义用户相关的 Pydantic 数据校验和序列化模型：创建请求、更新请求、完整响应、简要响应。所有模型均启用 `from_attributes=True` 以支持直接从 SQLAlchemy ORM 对象转换。

---

## 导入依赖

```python
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
```

| 导入项 | 用途 |
|--------|------|
| `re` | 正则表达式校验用户名格式 |
| `Optional` | 可选字段类型注解 |
| `field_validator` | Pydantic v2 字段级校验装饰器 |
| `ConfigDict` | Pydantic v2 模型配置字典 |

---

## 类详解

### `UserBase` — 用户共用字段

```python
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="用户名，字母数字下划线组成")
    nickname: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[list[str]] = Field(default_factory=list, max_length=10)
```

| 字段 | 类型 | 默认值 | 校验规则 |
|------|------|--------|----------|
| `username` | `str` | 必填 | 3~50 字符 |
| `nickname` | `Optional[str]` | `None` | 最长 100 字符 |
| `avatar_url` | `Optional[str]` | `None` | 最长 500 字符 |
| `bio` | `Optional[str]` | `None` | 最长 500 字符 |
| `tags` | `Optional[list[str]]` | `[]` | 最多 10 个标签 |

#### `validate_username(cls, v)` — 校验用户名格式

```python
@field_validator("username")
@classmethod
def validate_username(cls, v: str) -> str:
    v = v.strip()
    if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
        raise ValueError("用户名只能包含字母、数字和下划线，长度3-50")
    return v
```

| 属性 | 说明 |
|------|------|
| **装饰器** | `@field_validator("username")` — Pydantic v2 字段校验器，在 `username` 字段赋值后自动调用 |
| **类方法** | `@classmethod` — 不需要实例化即可调用 |
| **参数** | `cls` 类引用, `v: str` 原始输入值 |
| **返回值** | 校验和清洗后的字符串 |

**校验步骤**：

1. `v.strip()` — **去除首尾空格**，防止用户输入 `"  alice  "`
2. `re.match(r"^[a-zA-Z0-9_]{3,50}$", v)` — 正则匹配：
   - `^` 开头
   - `[a-zA-Z0-9_]` 只允许大小写字母、数字、下划线
   - `{3,50}` 长度 3~50
   - `$` 结尾
3. 不匹配则抛出 `ValueError`，Pydantic 会将此转换为 422 验证错误响应

#### `validate_tags(cls, v)` — 校验标签列表

```python
@field_validator("tags")
@classmethod
def validate_tags(cls, v: Optional[list[str]]) -> list[str]:
    if v is None:
        return []
    cleaned = []
    seen = set()
    for tag in v:
        tag = tag.strip()
        if not tag:
            continue
        if len(tag) > 30:
            raise ValueError(f"单个标签最多30个字符，超出: {tag}")
        if tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
    if len(cleaned) > 10:
        raise ValueError("标签最多10个")
    return cleaned
```

| 步骤 | 逻辑 | 说明 |
|------|------|------|
| 1 | `v is None → return []` | NULL 转为空列表 |
| 2 | `tag.strip()` | 去除每个标签的首尾空格 |
| 3 | `if not tag: continue` | 过滤空字符串和纯空格标签 |
| 4 | `if len(tag) > 30: raise` | 单个标签最长为 30 字符 |
| 5 | `if tag not in seen` | **去重**：相同的标签只保留第一次出现 |
| 6 | `if len(cleaned) > 10: raise` | 总标签数不超过 10 个 |

### `UserCreate` — 创建用户请求

```python
class UserCreate(UserBase):
    pass
```

完全继承 `UserBase` 的所有字段和校验器，不添加任何新字段。创建用户时，所有 `UserBase` 字段都可以传入。

### `UserUpdate` — 更新用户请求（部分更新）

```python
class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[list[str]] = Field(default=None)
```

| 字段 | 说明 |
|------|------|
| 全部字段 | 默认值均为 `None`，表示"未传入，不更新此字段" |
| `username` | **不在更新字段中**，用户名创建后不可更改 |

> **注意**：`UserUpdate` 不继承 `UserBase`，因为创建和更新的字段集合不同（更新时不允许修改 username）。

#### `validate_tags(cls, v)` — 标签校验（Update 版）

```python
@field_validator("tags")
@classmethod
def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
    if v is None:
        return None        # ← 注意：返回 None 而非 []！
    cleaned = []
    seen = set()
    for tag in v:
        tag = tag.strip()
        if not tag:
            continue
        if len(tag) > 30:
            raise ValueError(f"单个标签最多30个字符，超出: {tag}")
        if tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
    if len(cleaned) > 10:
        raise ValueError("标签最多10个")
    return cleaned
```

与 `UserBase.validate_tags` 的关键区别：

| 对比项 | `UserBase` | `UserUpdate` |
|--------|------------|-------------|
| `v is None` 时返回 | `[]`（空列表） | `None`（不更新） |
| 语义 | 创建时的默认值 | 更新时的"跳过"信号 |

返回 `None` 保证在 `user_service.update_user()` 中通过 `model_dump(exclude_unset=True)` 排除该字段。

### `UserResponse` — 用户信息响应

```python
class UserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    tags: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `from_attributes` | `True` | 关键配置！允许从 ORM 对象属性直接创建 Pydantic 模型。等价于 v1 的 `orm_mode = True` |

启用 `from_attributes=True` 后：

```python
user_orm = db.query(User).first()         # SQLAlchemy ORM 对象
user_response = UserResponse.model_validate(user_orm)  # 自动转换！
```

### `UserBrief` — 用户简要信息

```python
class UserBrief(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)
```

| 用途 | 说明 |
|------|------|
| 好友列表 | 不需要 `bio`、`created_at`、`updated_at` |
| 共同好友 | 仅需基本身份信息 |
| 推荐结果 | 推荐卡片展示 |

相比 `UserResponse`，`UserBrief` 省略了 `bio`、`created_at`、`updated_at` 三个字段，减少网络传输量。

---

## 函数汇总

| 函数/方法 | 所属类 | 说明 |
|-----------|--------|------|
| `validate_username(cls, v)` | `UserBase` | 正则校验用户名：去空格、只允许 `[a-zA-Z0-9_]`、长度 3-50 |
| `validate_tags(cls, v)` | `UserBase` | 校验标签列表：去重、去空、限制单标签 30 字符、总数 10 个 |
| `validate_tags(cls, v)` | `UserUpdate` | 同上，但 `v is None` 时返回 `None`（表示不更新字段） |
| `model_validate()` | `UserResponse` | 从 ORM 对象或字典构建响应模型（继承自 BaseModel） |
| `model_validate()` | `UserBrief` | 同上 |
