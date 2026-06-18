# -*- coding: utf-8 -*-
"""
依赖注入 — DB session、配置等
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """异步数据库会话依赖注入"""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
