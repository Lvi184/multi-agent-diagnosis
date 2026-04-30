#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础接口 - 健康检查、版本信息
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    app: str
    version: str
    env: str


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """
    检查服务是否正常运行
    
    返回示例：
    {
        "status": "ok",
        "app": "AI 心理健康筛查系统",
        "version": "2.0.0",
        "env": "development"
    }
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@router.get("/version", summary="版本信息")
async def get_version():
    """获取详细的版本信息"""
    return {
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug_mode": settings.DEBUG,
        "database_engine": settings.DB_ENGINE,
    }
