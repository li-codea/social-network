# 应用入口：FastAPI 主文件

> **源码文件**：`backend/app/main.py`

---

## 文件职责

FastAPI 应用的总入口。负责：应用生命周期管理（启动建表 / 关闭清理）、CORS 中间件配置、注册所有 API 路由器、提供健康检查端点。

启动命令：

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档地址：
- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

---

## 导入依赖

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, friendships, chat
```

| 导入项 | 用途 |
|--------|------|
| `asynccontextmanager` | 将异步生成器函数装饰为异步上下文管理器 |
| `FastAPI` | FastAPI 应用类 |
| `CORSMiddleware` | 跨域资源共享中间件 |
| `engine` | SQLAlchemy 引擎（建表、关闭连接池） |
| `Base` | ORM 基类（`Base.metadata.create_all` 建表） |
| `users, friendships, chat` | 三个路由模块 |

---

## 函数详解

### `lifespan(app: FastAPI)` — 应用生命周期管理

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    await engine.dispose()
```

| 属性 | 说明 |
|------|------|
| **装饰器** | `@asynccontextmanager` — 将异步生成器转为上下文管理器 |
| **参数** | `app: FastAPI` — FastAPI 应用实例 |
| **Startup 阶段** | `yield` 之前的代码：`Base.metadata.create_all(bind=engine)` 创建所有 ORM 表（仅在表不存在时创建，不会覆盖已有表）。**仅适合开发环境**，生产环境应使用 Alembic 数据库迁移工具 |
| **Running 阶段** | `yield` — 应用正常运行期间挂起 |
| **Shutdown 阶段** | `yield` 之后的代码：`await engine.dispose()` 关闭数据库连接池，释放所有连接资源 |

### `health_check()` — 健康检查端点

```python
@app.get("/api/v1/health", tags=["系统"], summary="健康检查")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
```

| 属性 | 说明 |
|------|------|
| **HTTP 方法** | `GET` |
| **路径** | `/api/v1/health` |
| **OpenAPI 分组** | `tags=["系统"]` 在 Swagger UI 中归入"系统"分组 |
| **返回值** | `{"status": "ok", "version": "1.0.0"}` |
| **用途** | 供负载均衡器、Kubernetes 探针、监控系统检测服务是否存活 |

---

## 模块级代码

### FastAPI 应用实例化

```python
app = FastAPI(
    title="社交网络好友推荐系统 API",
    description=(
        "基于共同好友与兴趣标签的社交网络好友推荐引擎。\n\n"
        "**核心技术**：CTE 递归查询、INTERSECT 运算符、JSON_OVERLAPS 标签匹配"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `title` | `"社交网络好友推荐系统 API"` | OpenAPI 文档标题 |
| `description` | 含 Markdown 的字符串 | 文档描述，列出核心技术栈 |
| `version` | `"1.0.0"` | API 版本号 |
| `lifespan` | `lifespan` 函数 | 应用生命周期回调 |
| `docs_url` | `"/docs"` | Swagger UI 路径 |
| `redoc_url` | `"/redoc"` | ReDoc 路径 |

### CORS 中间件配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite 默认端口
        "http://localhost:3000",   # 备用端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `allow_origins` | 4 个前端开发地址 | 白名单模式，仅允许这 4 个来源跨域访问 |
| `allow_credentials` | `True` | 允许携带 Cookie 和 Authorization 头 |
| `allow_methods` | `["*"]` | 允许所有 HTTP 方法（GET/POST/PUT/DELETE 等） |
| `allow_headers` | `["*"]` | 允许所有请求头 |

### 路由器注册

```python
app.include_router(users.router, prefix="/api/v1")
app.include_router(friendships.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
```

| 路由器 | 内部前缀 | 最终路径示例 |
|--------|---------|-------------|
| `users.router` | `/users` | `/api/v1/users/` |
| `friendships.router` | `/friendships` | `/api/v1/friendships/` |
| `chat.router` | `/messages` | `/api/v1/messages/` |

每个路由器内部已定义了各自的 `prefix`，这里再加 `/api/v1` 作为全局前缀，实现 API 版本化。

---

## 函数汇总

| 函数 | 装饰器/说明 | 作用 |
|------|------------|------|
| `lifespan(app)` | `@asynccontextmanager` | 启动时建表、关闭时释放连接池 |
| `health_check()` | `@app.get("/api/v1/health")` | 健康检查端点，返回服务状态 |
