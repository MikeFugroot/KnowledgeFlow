# -*- coding: utf-8 -*-
"""
加密工具 — Fernet (AES-256-CBC) 对称加密/解密
用于敏感配置（API Key、Cookie等）的加密存储
"""

from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _get_fernet() -> Fernet:
    """获取 Fernet 实例（使用配置中的密钥）"""
    key = settings.FERNET_KEY.encode() if isinstance(settings.FERNET_KEY, str) else settings.FERNET_KEY
    return Fernet(key)


def encrypt_value(plain_text: str) -> str:
    """
    加密字符串

    Args:
        plain_text: 明文字符串

    Returns:
        加密后的 Base64 字符串
    """
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_value(encrypted_text: str) -> str:
    """
    解密字符串

    Args:
        encrypted_text: 加密后的 Base64 字符串

    Returns:
        解密后的明文字符串
    """
    if not encrypted_text:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # 如果解密失败，可能是明文存储的非敏感配置，直接返回
        return encrypted_text


def is_encrypted(value: str) -> bool:
    """
    判断值是否已加密（Fernet 加密值总是以 gAAAA 开头）
    """
    if not value:
        return False
    return value.startswith("gAAAA")


def generate_key() -> str:
    """生成新的 Fernet 密钥（用于初始化部署）"""
    return Fernet.generate_key().decode("utf-8")
