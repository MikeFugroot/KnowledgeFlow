# -*- coding: utf-8 -*-
"""
配置管理服务 — 加密存储 + 动态配置读取
敏感配置（API Key、Cookie）使用 Fernet 加密存储在 SystemConfig 表
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig
from app.utils.crypto import encrypt_value, decrypt_value, is_encrypted

logger = logging.getLogger(__name__)

# 敏感配置键列表（这些键的值会自动加密存储）
SENSITIVE_KEYS = {
    "DASHSCOPE_API_KEY",
    "DEEPSEEK_API_KEY",
    "BILIBILI_COOKIE",
    "XHS_COOKIE",
    "FERNET_KEY",
}


class ConfigManager:
    """配置管理器"""

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}

    async def get_all_configs(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """获取所有配置项（解密后返回）"""
        stmt = select(SystemConfig).order_by(SystemConfig.key)
        result = await db.execute(stmt)
        configs = result.scalars().all()

        items = []
        for config in configs:
            value = decrypt_value(config.value_encrypted) if is_encrypted(config.value_encrypted) else config.value_encrypted
            items.append({
                "key": config.key,
                "value": value,
                "value_type": config.value_type,
                "description": config.description,
                "is_sensitive": config.key in SENSITIVE_KEYS,
            })
        return items

    async def get_config(self, db: AsyncSession, key: str) -> Optional[str]:
        """获取单个配置值（解密后返回）"""
        # 先查缓存
        if key in self._cache:
            return self._cache[key]

        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if config is None:
            return None

        value = decrypt_value(config.value_encrypted) if is_encrypted(config.value_encrypted) else config.value_encrypted
        self._cache[key] = value
        return value

    async def set_config(
        self,
        db: AsyncSession,
        key: str,
        value: str,
        value_type: str = "string",
        description: str = "",
    ) -> SystemConfig:
        """设置配置项（敏感值自动加密）"""
        # 清除缓存
        self._cache.pop(key, None)

        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        # 敏感配置加密存储
        stored_value = encrypt_value(value) if key in SENSITIVE_KEYS and value else value

        if config is not None:
            config.value_encrypted = stored_value
            config.value_type = value_type
            if description:
                config.description = description
        else:
            config = SystemConfig(
                key=key,
                value_encrypted=stored_value,
                value_type=value_type,
                description=description,
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)
        return config

    async def update_configs(self, db: AsyncSession, configs: List[Dict[str, Any]]) -> int:
        """批量更新配置"""
        updated = 0
        for item in configs:
            await self.set_config(
                db,
                key=item["key"],
                value=item["value"],
                value_type=item.get("value_type", "string"),
                description=item.get("description", ""),
            )
            updated += 1
        return updated

    async def delete_config(self, db: AsyncSession, key: str) -> bool:
        """删除配置项"""
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            return False
        await db.delete(config)
        await db.commit()
        self._cache.pop(key, None)
        return True

    async def init_default_configs(self, db: AsyncSession) -> None:
        """初始化默认配置项（首次启动时调用）"""
        from app.config import settings

        defaults = [
            ("API_PROVIDER", settings.API_PROVIDER, "string", "LLM 提供者: qwen/deepseek"),
            ("DASHSCOPE_API_KEY", settings.DASHSCOPE_API_KEY, "string", "通义千问 API Key"),
            ("DEEPSEEK_API_KEY", settings.DEEPSEEK_API_KEY, "string", "DeepSeek API Key"),
            ("BILIBILI_COOKIE", settings.BILIBILI_COOKIE, "string", "B站 Cookie（SESSDATA 等）"),
            ("XHS_COOKIE", settings.XHS_COOKIE, "string", "小红书 Cookie"),
            ("EMBEDDING_MODEL_NAME", settings.EMBEDDING_MODEL_NAME, "string", "Embedding 模型名称"),
            ("USE_RULE_FALLBACK", str(settings.USE_RULE_FALLBACK), "boolean", "LLM 不可用时是否启用规则兜底"),
            ("USE_LLM_PROFILE_GENERATION", str(settings.USE_LLM_PROFILE_GENERATION), "boolean", "是否启用 LLM 知识画像"),
        ]

        for key, value, value_type, description in defaults:
            stmt = select(SystemConfig).where(SystemConfig.key == key)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is None and value:
                await self.set_config(db, key=key, value=value, value_type=value_type, description=description)

    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._cache.clear()


# 全局配置管理器实例
config_manager = ConfigManager()
