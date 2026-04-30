#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置 - Loguru 结构化日志
"""
import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """配置日志"""
    
    # 移除默认的 stderr 处理器
    logger.remove()
    
    # ===== 1. 控制台输出（开发环境带颜色）=====
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stderr,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG,
    )
    
    # ===== 2. 普通日志文件（按天滚动）=====
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} | {message}"
    )
    logger.add(
        settings.LOG_DIR / "app_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="INFO",
        rotation="00:00",  # 每天 0 点滚动
        retention="30 days",  # 保留 30 天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )
    
    # ===== 3. 错误日志文件（单独保存）=====
    logger.add(
        settings.LOG_DIR / "error_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation="00:00",
        retention="60 days",
        compression="zip",
        encoding="utf-8",
    )
    
    # ===== 4. 诊断专用日志（用于分析用户数据）=====
    diagnosis_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "session_id={extra[session_id]} | "
        "user_id={extra[user_id]} | "
        "{level: <8} | "
        "{message}"
    )
    logger.add(
        settings.LOG_DIR / "diagnosis_{time:YYYY-MM-DD}.log",
        format=diagnosis_format,
        level="INFO",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
        filter=lambda record: "diagnosis" in record["extra"],
    )
    
    logger.info("日志系统初始化完成")
    return logger


# 诊断专用日志（绑定上下文）
class DiagnosisLogger:
    """诊断日志（带 session_id 上下文）"""
    
    def __init__(self, session_id: str, user_id: int = None):
        self.session_id = session_id
        self.user_id = user_id
        self.log = logger.bind(diagnosis=True, session_id=session_id, user_id=user_id or "anonymous")
    
    def info(self, message: str):
        self.log.info(message)
    
    def warning(self, message: str):
        self.log.warning(message)
    
    def error(self, message: str):
        self.log.error(message)
    
    def success(self, message: str):
        self.log.info(f"✅ {message}")


# 全局日志实例
app_logger = logger
