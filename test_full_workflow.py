#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整工作流
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json

print("=" * 60)
print("测试完整多 Agent 诊断工作流")
print("=" * 60)

from app.schemas.diagnosis import DiagnosisRequest
from app.core.orchestrator import DiagnosisOrchestrator

request = DiagnosisRequest(
    session_id="demo-session-001",
    text="我最近两个月情绪低落、失眠、没兴趣，也经常焦虑担心，偶尔觉得活着没有意义。",
    age=22,
    gender="female",
    scale_answers={"PHQ9": 16, "GAD7": 11},
    history=["无明确精神科就诊史"],
)

print(f"\n患者信息:")
print(f"  主诉: {request.text}")
print(f"  年龄: {request.age}")
print(f"  性别: {request.gender}")
print(f"  PHQ-9: {request.scale_answers.get('PHQ9')}")
print(f"  GAD-7: {request.scale_answers.get('GAD7')}")

print("\n正在执行诊断流程...\n")

response = DiagnosisOrchestrator().run(request)
result = response.model_dump()

print("=" * 60)
print("执行结果")
print("=" * 60)

print(f"\nSession ID: {result.get('session_id')}")

print(f"\n【Agent 执行轨迹】")
for trace in result.get('agent_traces', []):
    agent_name = trace.get('agent', '')
    summary = trace.get('summary', '')
    print(f"  ✓ {agent_name}")

report = result.get('report', {})
print(f"\n【诊断报告】")
print(f"  疑似诊断: {result.get('suspected_diagnosis', '未提供')}")
print(f"  风险等级: {result.get('risk_level', '未评估')}")
print(f"  建议: {result.get('recommendations', '未提供')}")

print("\n" + "=" * 60)
print("完整工作流测试成功！")
print("=" * 60)
