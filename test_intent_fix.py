#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试意图判断修复效果
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.agents.intent_classifier import get_intent_classifier, IntentType


def test_intent_classification():
    """测试各种场景的意图分类"""
    print("=" * 60)
    print("意图分类器测试")
    print("=" * 60)
    
    clf = get_intent_classifier()
    
    test_cases = [
        # (测试文本, 预期意图, 描述)
        ("你好", IntentType.GREETING, "简单问候"),
        ("你好！", IntentType.GREETING, "问候带感叹号"),
        ("hi", IntentType.GREETING, "英文问候"),
        ("在吗", IntentType.GREETING, "询问在线"),
        
        ("谢谢", IntentType.THANKS, "感谢"),
        ("谢谢你", IntentType.THANKS, "感谢你"),
        
        ("再见", IntentType.GOODBYE, "道别"),
        ("拜拜", IntentType.GOODBYE, "道别"),
        
        ("你是谁", IntentType.QUESTION_SYSTEM, "询问系统身份"),
        ("你能做什么", IntentType.QUESTION_SYSTEM, "询问系统功能"),
        ("怎么使用", IntentType.QUESTION_SYSTEM, "询问使用方法"),
        
        ("抑郁症怎么办", IntentType.QUESTION_MEDICAL, "询问医学问题"),
        ("失眠怎么治疗", IntentType.QUESTION_MEDICAL, "询问治疗方法"),
        
        ("情绪低落", IntentType.SYMPTOM_REPORT, "单症状报告"),
        ("最近2个月情绪低落，睡不着", IntentType.SYMPTOM_REPORT, "多症状报告"),
        ("最近情绪低落，对事情没兴趣，有时觉得不想活", IntentType.SYMPTOM_REPORT, "完整症状描述"),
        
        ("PHQ9: 18, GAD7: 11", IntentType.SYMPTOM_REPORT, "带量表分数"),
        
        ("哦", IntentType.CHITCHAT, "简单语气词"),
        ("嗯", IntentType.CHITCHAT, "简单回复"),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_intent, description in test_cases:
        intent, confidence = clf.classify(text)
        should_enter = clf.should_enter_diagnosis(intent)
        
        status = "[PASS]" if intent == expected_intent else "[FAIL]"
        if intent == expected_intent:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} [{description}]")
        print(f"   输入: {text}")
        print(f"   意图: {intent} (预期: {expected_intent})")
        print(f"   置信度: {confidence:.2f}")
        print(f"   进入诊断流程: {'是' if should_enter else '否'}")
        if not should_enter:
            print(f"   示例回复: {clf.get_response(intent)[:50]}...")
        print()
    
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("边界情况测试")
    print("=" * 60)
    
    clf = get_intent_classifier()
    
    edge_cases = [
        ("你好，我最近睡不着", "问候+症状，应该进入诊断"),
        ("我情绪很低落，怎么办？", "症状+问题，应该进入诊断"),
        ("", "空文本"),
        ("   ", "空白字符"),
        ("aaaaaaaaaaaaaaaaaaaaa", "无意义文本"),
    ]
    
    for text, description in edge_cases:
        intent, confidence = clf.classify(text)
        should_enter = clf.should_enter_diagnosis(intent)
        
        print(f"[{description}]")
        print(f"   输入: '{text}'")
        print(f"   意图: {intent}")
        print(f"   置信度: {confidence:.2f}")
        print(f"   进入诊断流程: {'是' if should_enter else '否'}")
        print()


if __name__ == '__main__':
    success = test_intent_classification()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] 所有测试通过！意图分类器工作正常。")
        print()
        print("修复效果说明：")
        print("  1. 用户说 '你好' -> 识别为问候，直接友好回复，不进入诊断")
        print("  2. 用户说 '谢谢' -> 识别为感谢，直接回复，不进入诊断")
        print("  3. 用户问 '你是谁' -> 识别为系统问题，直接回答，不进入诊断")
        print("  4. 用户描述症状 -> 正常进入10个Agent完整诊断流程")
        print()
        print("现在重启后端服务即可生效！")
    else:
        print("[ERROR] 部分测试失败，请检查。")
    print("=" * 60)
