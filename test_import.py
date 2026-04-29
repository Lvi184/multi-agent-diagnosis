#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单导入测试
"""
print("1. 测试配置导入...")
from app.core.config import settings
print(f"   配置加载成功: {settings.app_name}")

print("2. 测试Schema导入...")
from app.schemas.diagnosis import DiagnosisRequest
print("   Schema导入成功")

print("3. 测试Orchestrator导入...")
from app.core.orchestrator import DiagnosisOrchestrator
print("   Orchestrator导入成功")

print("4. 测试Workflow导入...")
from app.graph.workflow import LangGraphDiagnosisWorkflow
print("   Workflow导入成功")

print()
print("所有导入测试通过！")
print()
print("配置信息:")
print(f"  - API Key 已配置: {'是' if settings.deepseek_api_key else '否'}")
print(f"  - LLM Provider: {settings.llm_provider}")
print(f"  - 模型: {settings.deepseek_model}")
print(f"  - 使用真实LangGraph: {settings.use_real_langgraph}")
