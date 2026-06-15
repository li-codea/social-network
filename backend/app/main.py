"""
FastAPI 应用入口

功能：
- lifespan 启动时自动创建数据库表（开发便利）
- 注册所有 API 路由器
- 配置 CORS 中间件以支持 Vue 前端跨域请求
- health check 端点用于可用性探测

启动方式：
    cd backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

API 文档：
    Swagger UI:  http://localhost:8000/docs
    ReDoc:       http://localhost:8000/redoc
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, friendships, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    Startup: 创建所有 ORM 表（若不存在）
    Shutdown: 释放数据库连接池
    """
    # 开发阶段自动建表，生产环境应使用 Alembic 迁移
    Base.metadata.create_all(bind=engine)
    yield
    # 在应用关闭时清理连接池
    await engine.dispose()


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

# CORS 中间件：允许 Vue 开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:3000",  # 备用端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由器
app.include_router(users.router, prefix="/api/v1")
app.include_router(friendships.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["系统"], summary="健康检查")
async def health_check():
    """服务可用性探测端点"""
    return {"status": "ok", "version": "1.0.0"}
