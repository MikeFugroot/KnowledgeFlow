# -*- coding: utf-8 -*-
"""
KnowledgeFlow Web 版 — FastAPI 应用入口

功能：
- CORS 跨域配置
- 路由挂载（8 个路由模块）
- WebSocket 端点
- 生命周期事件（启动时初始化数据库、加载索引）
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, async_engine, sync_engine
from app.routers import (
    upload,
    document,
    webimport,
    search,
    profile,
    task,
    settings as settings_router,
    ws,
)
from app.services.search_engine import search_engine
from app.services.task_manager import task_manager
from app.services.config_manager import config_manager
from app.routers.ws import ws_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def is_access_allowed(request: Request) -> bool:
    if not settings.ACCESS_CODE:
        return True

    supplied_code = (
        request.headers.get("X-KF-Access-Code")
        or request.query_params.get("kf_access_code")
        or ""
    )
    return supplied_code == settings.ACCESS_CODE


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ---- 启动时 ----
    logger.info("KnowledgeFlow Web 版启动中...")

    # 确保数据目录
    settings.ensure_data_dirs()

    # 创建数据库表（开发环境自动创建，生产环境用 Alembic 迁移）
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表已就绪")

    # 初始化默认配置
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await config_manager.init_default_configs(db)
    logger.info("默认配置已初始化")

    # 设置任务管理器的 WebSocket 引用
    task_manager.set_ws_manager(ws_manager)

    # 尝试从磁盘加载已有向量索引
    if search_engine.load_index_from_disk():
        logger.info(f"向量索引已从磁盘加载：{search_engine.total_chunks} 个文本块")
    else:
        logger.info("未找到已有向量索引，请通过 API 触发索引构建")

    logger.info(f"KnowledgeFlow Web 版已启动：http://{settings.HOST}:{settings.PORT}")

    yield

    # ---- 关闭时 ----
    logger.info("KnowledgeFlow Web 版关闭中...")
    await async_engine.dispose()
    logger.info("数据库连接已关闭")


# ---- 创建 FastAPI 应用 ----
app = FastAPI(
    title="KnowledgeFlow API",
    description="个人知识整理系统 Web 版后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# ---- CORS 配置 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_code_middleware(request: Request, call_next):
    path = request.url.path
    public_paths = {"/api/health", "/api/auth/login"}
    protected = path.startswith("/api/") or path.startswith("/static/uploads")
    public = path in public_paths or request.method == "OPTIONS"

    if protected and not public and not is_access_allowed(request):
        return JSONResponse(
            status_code=401,
            content={"detail": "访问口令不正确或缺失"},
        )

    return await call_next(request)

# ---- 注册路由 ----
app.include_router(upload.router)
app.include_router(document.router)
app.include_router(webimport.router)
app.include_router(search.router)
app.include_router(profile.router)
app.include_router(task.router)
app.include_router(settings_router.router)
app.include_router(ws.router)

# ---- 挂载静态文件目录（让前端可以访问上传的文件）----
from pathlib import Path as _Path
uploads_dir = _Path(settings.UPLOAD_DIR)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# ---- 健康检查 ----
@app.post("/api/auth/login", tags=["系统"])
async def access_login(payload: dict = Body(default_factory=dict)):
    """校验访问口令。"""
    code = str(payload.get("code", ""))
    if not settings.ACCESS_CODE or code == settings.ACCESS_CODE:
        return {"code": 0, "data": {"ok": True}, "message": "success"}

    return JSONResponse(
        status_code=401,
        content={"detail": "访问口令不正确"},
    )


@app.get("/api/health", tags=["系统"])
async def health_check() -> dict:
    """健康检查端点"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "index_ready": search_engine.is_ready,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
