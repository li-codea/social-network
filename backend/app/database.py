"""
数据库会话管理模块
使用 FastAPI 依赖注入模式管理 SQLAlchemy 会话生命周期
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# 创建 MySQL 引擎，启用连接池和连接健康检查
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,  # 使用前验证连接有效性
    echo=settings.DB_ECHO,  # 开发时可设为 true 查看 SQL 日志
)

# 会话工厂，每个请求获取一个独立会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类，所有模型继承自此类
Base = declarative_base()


def get_db():
    """
    FastAPI 依赖注入函数，为每个请求提供数据库会话
    请求结束时自动关闭会话并回滚未提交的事务
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
