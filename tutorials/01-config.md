# 配置层：Settings 类详解

> **源码文件**：`backend/app/config.py`

---

## 文件职责

通过 `pydantic-settings` 库从 `.env` 文件和环境变量中加载数据库连接参数，并提供构建 MySQL 连接 URL 的属性方法。

---

## 导入依赖

```python
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings
```

| 导入项 | 用途 |
|--------|------|
| `quote_plus` | URL 编码用户名和密码，防止 `@` `/` `:` 等特殊字符破坏 URL 格式 |
| `BaseSettings` | pydantic-settings 的基类，自动从 `.env` 文件和环境变量读取配置 |

---

## 类：`Settings(BaseSettings)`

继承自 `BaseSettings`，拥有自动从 `.env` 文件读取同名环境变量的能力。

### 类属性（配置字段）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `DB_HOST` | `str` | `"localhost"` | MySQL 服务器地址 |
| `DB_PORT` | `int` | `3306` | MySQL 端口号 |
| `DB_USER` | `str` | `"root"` | 数据库用户名 |
| `DB_PASSWORD` | `str` | `""` | 数据库密码 |
| `DB_NAME` | `str` | `"social_network"` | 数据库名称 |
| `DB_ECHO` | `bool` | `False` | 是否打印 SQL 日志（开发调试用） |

这些字段会自动从项目根目录的 `.env` 文件中读取同名的环境变量。例如 `.env` 文件内容：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mysecret
DB_NAME=social_network
DB_ECHO=False
```

### 属性方法

#### `DATABASE_URL(self) -> str`

```python
@property
def DATABASE_URL(self) -> str:
    encoded_user = quote_plus(self.DB_USER)
    encoded_password = quote_plus(self.DB_PASSWORD)
    return (
        f"mysql+pymysql://{encoded_user}:{encoded_password}"
        f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        f"?charset=utf8mb4"
    )
```

| 属性 | 说明 |
|------|------|
| **类型** | `@property` 计算属性，调用时无需括号 |
| **返回值** | MySQL 连接 URL 字符串 |
| **URL 格式** | `mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4` |

**实现细节**：

1. **URL 编码**：使用 `quote_plus()` 对用户名和密码进行百分号编码，防止特殊字符（如 `@` `:` `/` `#`）破坏 URL 结构
2. **数据库驱动**：使用 `pymysql` 作为 MySQL 的 Python 驱动（纯 Python 实现，无需安装 MySQL 客户端库）
3. **字符集**：强制指定 `utf8mb4`（完整的 UTF-8 支持，包括 emoji 等 4 字节字符）

### 类配置

```python
model_config = {
    "env_file": ".env",
    "env_file_encoding": "utf-8",
    "case_sensitive": True,
}
```

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `env_file` | `".env"` | 指定环境变量文件名，位于项目根目录 |
| `env_file_encoding` | `"utf-8"` | `.env` 文件的字符编码 |
| `case_sensitive` | `True` | 环境变量名大小写敏感（`DB_HOST` 和 `db_host` 被视为不同变量） |

---

## 模块级实例

```python
settings = Settings()
```

| 变量 | 说明 |
|------|------|
| `settings` | `Settings` 类的全局单例，项目启动时自动加载 `.env` 配置，其他模块通过 `from app.config import settings` 引用 |

---

## 函数汇总

| 函数/方法 | 类型 | 说明 |
|-----------|------|------|
| `Settings.__init__()` | 构造函数（继承） | 自动从 `.env` 和环境变量加载配置字段 |
| `Settings.DATABASE_URL()` | `@property` 计算属性 | 构建 pymysql 连接 URL，含 URL 编码和 utf8mb4 字符集 |
