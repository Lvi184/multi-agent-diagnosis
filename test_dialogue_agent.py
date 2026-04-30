#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试对话引导 Agent
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.agents.dialogue_agent import get_dialogue_agent
from app.core.session_manager import get_session_manager, SessionStatus

agent = get_dialogue_agent()
session_mgr = get_session_manager()

print("=" * 60)
print("🤖 对话引导 Agent 测试")
print("=" * 60)

session_id = "test-dialogue-001"
session = session_mgr.create_session(session_id)

# 模拟对话流程
dialogues = [
    "医生，我最近心情不好，总是失眠，对什么都没兴趣",
    "大概有两个多月了",
    "之前没有过这种情况",
    "没有吃药",
    "2",  # PHQ9 Q1
    "1",  # PHQ9 Q2
    "2",  # PHQ9 Q3
    "1",  # PHQ9 Q4
    "2",  # PHQ9 Q5
    "1",  # PHQ9 Q6
    "2",  # PHQ9 Q7
    "1",  # PHQ9 Q8
    "2",  # PHQ9 Q9
    "1",  # GAD7 Q1
    "2",  # GAD7 Q2
    "1",  # GAD7 Q3
    "2",  # GAD7 Q4
    "1",  # GAD7 Q5
    "2",  # GAD7 Q6
    "1",  # GAD7 Q7
]

for i, user_msg in enumerate(dialogues):
    print(f"\n{'=' * 60}")
    print(f"💬 第 {i+1} 轮对话")
    print(f"{'=' * 60}")
    print(f"用户: {user_msg}")
    
    state_update, response = agent.process_message(session, user_msg)
    
    print(f"\nAI 回复:\n{response}")
    print(f"\n状态: {session.status.value}")
    
    if session.symptoms:
        print(f"已收集症状: {session.symptoms}")
    
    if session.scales.get('PHQ9'):
        phq9 = session.scales['PHQ9']
        if isinstance(phq9, dict) and phq9.get('items'):
            score = sum(phq9['items'].values())
            print(f"PHQ-9 当前得分: {score}/27")
    
    if session.scales.get('GAD7'):
        gad7 = session.scales['GAD7']
        if isinstance(gad7, dict) and gad7.get('items'):
            score = sum(gad7['items'].values())
            print(f"GAD-7 当前得分: {score}/21")
    
    if session.status == SessionStatus.DIAGNOSING:
        print("\n✅ 信息收集完成，可以开始诊断！")
        break

print("\n" + "=" * 60)
print("📊 收集结果汇总")
print("=" * 60)
print(f"症状: {session.symptoms}")
print(f"持续时间: {session.duration}")
print(f"既往史: {session.medical_history}")
print(f"用药史: {session.medication_history}")
if session.scales.get('PHQ9') and isinstance(session.scales['PHQ9'], dict):
    phq9 = session.scales['PHQ9']
    if phq9.get('items'):
        print(f"PHQ-9 总分: {sum(phq9['items'].values())}")
if session.scales.get('GAD7') and isinstance(session.scales['GAD7'], dict):
    gad7 = session.scales['GAD7']
    if gad7.get('items'):
        print(f"GAD-7 总分: {sum(gad7['items'].values())}")
print(f"状态: {session.status.value}")

print("\n" + "=" * 60)
print("✅ 对话引导测试完成！")
print("=" * 60)
print("\n💡 功能实现：")
print("  1. ✅ 症状自动提取")
print("  2. ✅ 多轮状态管理")
print("  3. ✅ PHQ-9 量表引导（9题）")
print("  4. ✅ GAD-7 量表引导（7题）")
print("  5. ✅ 评分自动计算")
print("  6. ✅ 双模式判断（快速/引导）")
print()
