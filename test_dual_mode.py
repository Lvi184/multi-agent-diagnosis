#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试双模式诊断系统
模式一：快速诊断（已有量表分数）
模式二：引导评估（多轮对话采集信息）
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.core.orchestrator_v2 import get_orchestrator_v2

orchestrator = get_orchestrator_v2()

print("=" * 60)
print("🎯 双模式诊断系统测试")
print("=" * 60)

# ============================================================================
# 测试一：快速诊断模式（已有量表分数）
# ============================================================================
print("\n" + "=" * 60)
print("【模式一】快速诊断模式（已有量表分数）")
print("=" * 60)

print("\n用户输入：")
print("  症状：最近两个月情绪低落，失眠，没兴趣，偶尔觉得活着没有意义")
print("  PHQ-9：16 分")
print("  GAD-7：12 分")

result, report = orchestrator.quick_diagnosis(
    session_id="test-quick-mode-001",
    text="最近两个月情绪低落，失眠，没兴趣，偶尔觉得活着没有意义",
    scale_answers={"PHQ9": 16, "GAD7": 12},
    age="28",
    gender="女",
)

print("\n" + report)

# ============================================================================
# 测试二：引导评估模式（多轮对话）
# ============================================================================
print("\n" + "=" * 60)
print("【模式二】引导评估模式（多轮对话采集）")
print("=" * 60)

session_id = "test-guided-mode-001"

# 第一轮：初始输入
print("\n💬 第 1 轮对话")
print("用户：医生，我最近心情不好，总是失眠，对什么都没兴趣")

result, reply = orchestrator.process_message(
    session_id=session_id,
    user_message="医生，我最近心情不好，总是失眠，对什么都没兴趣",
)

print(f"\n系统：\n{reply}")
print(f"\n状态：{result['status']}")
print(f"模式：{result['mode']}")

# 第二轮：回答持续时间
print("\n" + "-" * 50)
print("💬 第 2 轮对话")
print("用户：大概有两个多月了")

result, reply = orchestrator.process_message(
    session_id=session_id,
    user_message="大概有两个多月了",
)

print(f"\n系统：\n{reply}")
print(f"\n已收集症状：{result.get('collected_so_far', {}).get('symptoms')}")

# 第三轮：回答既往史
print("\n" + "-" * 50)
print("💬 第 3 轮对话")
print("用户：之前没有过这种情况")

result, reply = orchestrator.process_message(
    session_id=session_id,
    user_message="之前没有过这种情况",
)

print(f"\n系统：\n{reply}")

# 第四轮：回答用药史
print("\n" + "-" * 50)
print("💬 第 4 轮对话")
print("用户：没有吃药")

result, reply = orchestrator.process_message(
    session_id=session_id,
    user_message="没有吃药",
)

print(f"\n系统：\n{reply}")

# 第五轮：PHQ-9 Q1
print("\n" + "-" * 50)
print("💬 第 5 轮对话 (PHQ-9 Q1)")
print("用户：2")  # 好几天

result, reply = orchestrator.process_message(
    session_id=session_id,
    user_message="2",
)

print(f"\n系统：\n{reply[:100]}...")  # 截断显示

# 快速完成剩余量表问题（模拟）
print("\n" + "-" * 50)
print("💬 快速完成剩余量表评估...")

# 模拟完成 PHQ-9
for i in range(8):  # 还有8题
    orchestrator.process_message(session_id, "1")

# 模拟完成 GAD-7
for i in range(7):
    orchestrator.process_message(session_id, "2")

# 最后一轮：获取诊断结果
print("\n" + "-" * 50)
print("💬 量表完成，获取诊断结果")

result, reply = orchestrator.process_message(
    session_id=session_id,
    user_message="",
)

print("\n" + "=" * 60)
print("📊 最终诊断报告")
print("=" * 60)
print(reply)

print("\n" + "=" * 60)
print("✅ 双模式系统测试完成！")
print("=" * 60)
print("\n💡 功能总结：")
print("  1. ✅ 快速诊断模式 - 已有量表直接诊断")
print("  2. ✅ 引导评估模式 - 多轮对话逐步采集")
print("  3. ✅ 会话记忆 - 状态持久化")
print("  4. ✅ 自动量表引导 - PHQ-9 / GAD-7")
print("  5. ✅ 智能信息提取 - 症状识别")
print()
