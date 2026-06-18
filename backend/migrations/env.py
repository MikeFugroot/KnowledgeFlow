# -*- coding: utf-8 -*-
"""
Alembic 迁移环境配置
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import settings
from app.database import Base

# 导入所有模型，确保 Base.metadata 包含所有表定义
from app.models import (  # noqa: F401
    document,
    raw_doc,
    profile,
    search_index,
    task,
    system_config,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 使用异步数据库 URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式执行迁移"""
    section = config.get_section(config.config_ini_section, {})
    # alembic.ini 使用同步驱动（sqlite://），异步迁移需使用异步驱动（sqlite+aiosqlite://）
    section["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式：连接数据库执行迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
