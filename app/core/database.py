#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置 - Tortoise ORM
"""
from app.core.config import settings

# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": [
                "app.models",
            ],
            "default_connection": "default",
        },
    },
    # 时区设置
    "use_tz": True,
    "timezone": "Asia/Shanghai",
}


async def init_db():
    """初始化数据库连接"""
    from tortoise import Tortoise
    from app.core.logging_config import app_logger
    
    await Tortoise.init(config=TORTOISE_ORM)
    
    # 开发环境自动创建表（生产环境用 aerich migrate）
    if settings.DEBUG:
        await Tortoise.generate_schemas()
        app_logger.info("✅ 数据库表已创建（开发模式）")
    
    app_logger.info("✅ 数据库连接成功")


async def close_db():
    """关闭数据库连接"""
    from tortoise import Tortoise
    from app.core.logging_config import app_logger
    
    await Tortoise.close_connections()
    app_logger.info("✅ 数据库连接已关闭")
