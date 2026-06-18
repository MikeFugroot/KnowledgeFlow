# -*- coding: utf-8 -*-
"""
文件存储路径管理
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings


def get_upload_dir() -> Path:
    """获取上传目录"""
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_read_output_dir() -> Path:
    """获取解析输出目录"""
    path = Path(settings.READ_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_vector_index_dir() -> Path:
    """获取向量索引目录"""
    path = Path(settings.VECTOR_INDEX_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_web_cache_dir() -> Path:
    """获取网页缓存目录"""
    path = Path(settings.WEB_CACHE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    """获取数据根目录"""
    path = Path(settings.DATA_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_upload_path(filename: str, doc_type: str = "") -> Path:
    """
    生成按日期分目录的上传文件路径

    规则：uploads/2025-06/safe_filename.ext
    """
    upload_dir = get_upload_dir()
    now = datetime.now()
    date_dir = upload_dir / f"{now.year:04d}-{now.month:02d}"
    date_dir.mkdir(parents=True, exist_ok=True)

    # 安全文件名：添加时间戳防重名
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    from app.utils.text import safe_filename
    safe_name = safe_filename(f"{stem}_{now.strftime('%H%M%S')}")
    return date_dir / f"{safe_name}{suffix}"


def get_source_path(document_id: int, filename: str) -> Path:
    """根据文档ID查找上传的原始文件"""
    upload_dir = get_upload_dir()
    # 在所有日期目录中查找
    for date_dir in sorted(upload_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for f in date_dir.iterdir():
            if f.is_file() and f.name.startswith(filename.split(".")[0]):
                return f
    return Path()


def ensure_all_dirs() -> None:
    """确保所有数据目录存在"""
    for dir_func in [
        get_data_dir,
        get_upload_dir,
        get_read_output_dir,
        get_vector_index_dir,
        get_web_cache_dir,
    ]:
        dir_func()
