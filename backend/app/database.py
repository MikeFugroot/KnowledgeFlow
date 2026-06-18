# -*- coding: utf-8 -*-
"""
数据库引擎 + Session 工厂
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings


# ---- 同步引擎（用于 Alembic 迁移等场景 + 后台任务）----
sync_database_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace(
    "+asyncpg", ""
)
sync_engine = create_engine(
    sync_database_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in sync_database_url else {},
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# ---- 异步引擎（FastAPI 主应用使用）----
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


# ---- ORM 基类 ----
class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类"""
    pass


def get_sync_session() -> Session:
    """获取同步数据库会话（用于迁移脚本等场景）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
