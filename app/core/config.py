#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理 - 从环境变量读取，兼容 .env 文件
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


class Settings:
    """应用配置"""
    
    # ===== 基础配置 =====
    APP_NAME = os.getenv("APP_NAME", "AI 心理健康筛查系统")
    APP_VERSION = "2.0.0"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    APP_ENV = os.getenv("APP_ENV", "development")
    
    # ===== 安全配置（必须修改！）=====
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-please-2026")
    if len(SECRET_KEY) < 32 and APP_ENV == "production":
        raise ValueError("生产环境 SECRET_KEY 至少需要 32 字符")
    
    # ===== JWT 配置 =====
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "240"))  # 4小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 7天
    
    # ===== 数据库配置 =====
    DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "multi_agent_diagnosis")
    
    # SQLite 数据库路径
    SQLITE_PATH = Path(__file__).resolve().parents[2] / "data" / "db.sqlite3"
    
    @property
    def DATABASE_URL(self) -> str:
        """数据库连接 URL"""
        if self.DB_ENGINE == "sqlite":
            self.SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{self.SQLITE_PATH}"
        return f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # ===== CORS 配置 =====
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    
    # ===== Swagger 文档保护 =====
    SWAGGER_UI_USERNAME = os.getenv("SWAGGER_UI_USERNAME", "admin")
    SWAGGER_UI_PASSWORD = os.getenv("SWAGGER_UI_PASSWORD", "")
    
    # ===== 模型配置 =====
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
    
    # ===== DSM-5 知识图谱 =====
    DSM5_GRAPH_PATH = Path(__file__).resolve().parents[2] / "data" / "dsm5_graph.json"
    
    # ===== 限流配置 =====
    LOGIN_RATE_LIMIT = "5/minute"  # 登录每分钟 5 次
    DIAGNOSIS_RATE_LIMIT = "10/minute"  # 诊断每分钟 10 次
    
    # ===== 文件上传 =====
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES = [".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg"]
    UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
    
    # ===== 日志配置 =====
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
    
    def __init__(self):
        """初始化：确保必要的目录存在"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # ===== LLM 配置（兼容旧代码）=====
        self.deepseek_api_key = self.DEEPSEEK_API_KEY
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.deepseek_timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "120"))  # 超时时间（秒）
        self.openai_api_key = self.OPENAI_API_KEY
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.enable_llm = os.getenv("ENABLE_LLM", "true").lower() == "true"  # 是否启用 LLM
        
        # ===== LangGraph 配置（旧代码兼容）=====
        self.use_real_langgraph = os.getenv("USE_REAL_LANGGRAPH", "false").lower() == "true"
        self.use_langgraph = self.use_real_langgraph
        
        # ===== 工作流配置 =====
        self.workflow_mode = os.getenv("WORKFLOW_MODE", "fallback")  # langgraph / fallback</script>


# 全局单例
settings = Settings()
