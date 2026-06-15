# 数据库层：引擎与会话管理

> **源码文件**：`backend/app/database.py`

---

## 文件职责

使用 SQLAlchemy 创建 MySQL 数据库引擎、会话工厂和 ORM 基类，并通过 FastAPI 依赖注入模式管理每个 HTTP 请求的数据库会话生命周期。

---

## 导入依赖

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
```

| 导入项 | 用途 |
|--------|------|
| `create_engine` | 创建数据库引擎（连接池） |
| `sessionmaker` | 创建会话工厂类 |
| `declarative_base` | 创建 ORM 模型的基类 |
| `settings` | 从配置模块获取数据库连接 URL 和参数 |

---

## 模块级变量

### `engine` — 数据库引擎

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `settings.DATABASE_URL` | MySQL 连接 URL | 连接到 MySQL 数据库 |
| `pool_size` | `10` | 连接池常驻连接数 |
| `max_overflow` | `20` | 超出 pool_size 时最多额外创建的连接数（峰值最大 30 连接） |
| `pool_recycle` | `3600` | 连接最大存活时间（秒），超过后自动回收重连。防止 MySQL 8小时超时 |
| `pool_pre_ping` | `True` | 每次使用连接前发送 `SELECT 1` 验证连接有效性。防止使用已断开的连接 |
| `echo` | `settings.DB_ECHO` | 是否打印执行的 SQL 语句到控制台（开发调试开关） |

### `SessionLocal` — 会话工厂

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `autocommit` | `False` | 禁用自动提交，由开发者显式调用 `db.commit()` |
| `autoflush` | `False` | 禁用自动刷新（禁用查询前自动将 pending 变更同步到数据库） |
| `bind` | `engine` | 绑定到上面创建的 MySQL 引擎 |

### `Base` — ORM 模型基类

```python
Base = declarative_base()
```

所有 ORM 模型类（`User`、`Friendship`、`Message`）都继承自 `Base`。`Base.metadata` 包含了所有表的元数据，用于自动建表。

---

## 函数详解

### `get_db()` — FastAPI 依赖注入函数

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

| 属性 | 说明 |
|------|------|
| **用途** | FastAPI 依赖注入，为每个 HTTP 请求提供独立的数据库会话 |
| **返回值** | 生成器（Generator），每次 `yield` 一个 `Session` 对象 |
| **异常安全** | `finally` 块保证无论请求成功或失败，会话都会被关闭 |

**执行流程**：

1. **请求到达**：FastAPI 调用 `get_db()`，创建新的 `SessionLocal()` 实例
2. **处理请求**：`yield db` 将会话对象注入到路由处理函数中
3. **请求结束**：
   - 正常返回：`finally` 执行 `db.close()`，将会话归还连接池
   - 异常抛出：`finally` 仍然执行 `db.close()`，不会泄漏连接
   - 未提交的事务会被自动回滚（SQLAlchemy 默认行为）

**使用方式**（在路由函数中）：

```python
@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()
```

---

## 函数汇总

| 函数/变量 | 类型 | 说明 |
|-----------|------|------|
| `engine` | 模块变量 | SQLAlchemy 数据库引擎，管理 MySQL 连接池 |
| `SessionLocal` | 模块变量 | 会话工厂类，每次调用创建新会话 |
| `Base` | 模块变量 | ORM 模型基类，`Base.metadata` 持有所有表结构 |
| `get_db()` | 生成器函数 | FastAPI 依赖注入，请求开始创建会话，请求结束自动关闭 |
