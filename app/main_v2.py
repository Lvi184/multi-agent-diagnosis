#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Agent Diagnosis - AI 心理健康筛查系统 v2.0
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from app.core.config import settings
from app.core.logging_config import setup_logging, app_logger
from app.core.database import init_db, close_db

# ===== 日志初始化 =====
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    app_logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    app_logger.info(f"📊 环境: {settings.APP_ENV} | Debug: {settings.DEBUG}")
    
    # 数据库初始化
    await init_db()
    
    yield  # 应用运行中
    
    # 关闭时
    await close_db()
    app_logger.info("👋 应用已关闭")


# ===== FastAPI 应用 =====
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="企业级 AI 心理健康筛查系统 - 引导式多轮对话 + 多 Agent 诊断",
    lifespan=lifespan,
)

# ===== CORS 配置 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 路由注册（必须放在静态文件前面！）=====
from app.api.v1.auth import router as auth_router
from app.api.v1.dialogue import router as dialogue_router
from app.api.v1.diagnosis import router as diagnosis_router
from app.api.v1.base import router as base_router

app.include_router(base_router, prefix="/api/v1", tags=["基础接口"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证接口"])
app.include_router(dialogue_router, prefix="/api/v1/dialogue", tags=["对话接口"])
app.include_router(diagnosis_router, prefix="/api/v1/diagnosis", tags=["诊断接口"])

# ===== 静态文件服务（放在最后！）=====
# 把 frontend 目录挂载为根路径
frontend_path = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_v2:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
    )
