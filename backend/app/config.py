# -*- coding: utf-8 -*-
"""
全局配置模块 — 从 .env 加载配置，Pydantic BaseSettings
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，优先级：环境变量 > .env 文件 > 代码默认值"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 数据库 ----
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/knowledgeflow.db"

    # ---- LLM API ----
    API_PROVIDER: str = "qwen"  # qwen / deepseek
    DASHSCOPE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # Qwen 配置
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    QWEN_FILE_UPLOAD_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/files"
    QWEN_MODEL_NAME: str = "qwen-plus"
    QWEN_DOC_MODEL_NAME: str = "qwen-doc-turbo"
    USE_QWEN_DOC_TURBO_FOR_FILES: bool = True
    QWEN_DOC_UPLOAD_TIMEOUT: int = 180
    QWEN_DOC_PARSE_RETRY: int = 8

    # DeepSeek 配置
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/chat/completions"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # LLM 通用参数
    LLM_TIMEOUT: int = 90
    MAX_TEXT_CHARS_FOR_LLM: int = 8000
    USE_RULE_FALLBACK: bool = True
    CATEGORIES: List[str] = ["学习", "技术", "生活", "其他"]

    # ---- 加密 ----
    FERNET_KEY: str = ""

    # ---- 视频转写 ----
    WHISPER_BACKEND: str = "faster_whisper"
    WHISPER_MODEL_CANDIDATES: str = "large-v3,medium,small"
    WHISPER_LANGUAGE: str = "zh"
    WHISPER_BEAM_SIZE: int = 5
    FASTER_WHISPER_GPU_COMPUTE_TYPE: str = "int8_float16"
    FASTER_WHISPER_CPU_COMPUTE_TYPE: str = "int8"
    USE_LOCAL_FASTER_WHISPER_FIRST: bool = True
    LOCAL_FASTER_WHISPER_MODEL_DIR: str = "models/faster-whisper-large-v3"

    # ---- 支持的文件类型 ----
    SUPPORTED_EXTS: str = ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.jpg,.jpeg,.png,.gif,.bmp,.mp4,.mov,.avi,.mkv,.m4a,.mp3,.wav"
    VIDEO_EXTS: str = ".mp4,.mov,.avi,.mkv,.m4a,.mp3,.wav"
    QWEN_DOC_SUPPORTED_EXTS: str = ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.md,.txt,.jpg,.jpeg,.png,.gif,.bmp"

    # ---- 语义检索 ----
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    SEARCH_CHUNK_SIZE: int = 260
    SEARCH_CHUNK_OVERLAP: int = 80
    SEARCH_TOP_K: int = 8
    SEARCH_CANDIDATE_K: int = 80
    LEXICAL_CANDIDATE_K: int = 80
    SEARCH_BATCH_SIZE: int = 32

    # ---- 知识画像 ----
    USE_LLM_PROFILE_GENERATION: bool = True
    PROFILE_MAX_ITEMS_FOR_LLM: int = 40
    PROFILE_TIMEOUT: int = 90

    # ---- 网页导入 ----
    BILIBILI_COOKIE: str = ""
    XHS_COOKIE: str = ""
    WEB_IMPORT_MAX_VIDEOS: int = 20

    # ---- 文件存储路径 ----
    DATA_DIR: str = "./data"
    UPLOAD_DIR: str = "./data/uploads"
    READ_OUTPUT_DIR: str = "./data/read_output"
    VECTOR_INDEX_DIR: str = "./data/vector_index"
    WEB_CACHE_DIR: str = "./data/web_cache"

    # ---- 服务 ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ACCESS_CODE: str = "knowledgeflow"

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def supported_exts_set(self) -> set:
        """返回支持的文件扩展名集合"""
        return {ext.strip() for ext in self.SUPPORTED_EXTS.split(",") if ext.strip()}

    @property
    def video_exts_set(self) -> set:
        """返回视频文件扩展名集合"""
        return {ext.strip() for ext in self.VIDEO_EXTS.split(",") if ext.strip()}

    @property
    def qwen_doc_supported_exts_set(self) -> set:
        """返回 Qwen Doc Turbo 支持的文件扩展名集合"""
        return {ext.strip() for ext in self.QWEN_DOC_SUPPORTED_EXTS.split(",") if ext.strip()}

    @property
    def whisper_model_candidates_list(self) -> List[str]:
        """返回 Whisper 模型候选列表"""
        return [m.strip() for m in self.WHISPER_MODEL_CANDIDATES.split(",") if m.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        """返回 CORS 允许的来源列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def ensure_data_dirs(self) -> None:
        """确保所有数据目录存在"""
        for dir_path in [
            self.DATA_DIR,
            self.UPLOAD_DIR,
            self.READ_OUTPUT_DIR,
            self.VECTOR_INDEX_DIR,
            self.WEB_CACHE_DIR,
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


# 全局配置单例
settings = Settings()
