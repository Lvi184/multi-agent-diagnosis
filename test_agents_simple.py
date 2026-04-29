#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步测试各个 Agent
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 50)
print("开始测试各个 Agent")
print("=" * 50)

# 1. 测试 IntakeAgent
print("\n1. 测试 IntakeAgent...")
from app.agents.intake_agent import IntakeAgent
agent = IntakeAgent()

class MockRequest:
    text = "我最近两个月情绪低落、失眠、没兴趣"
    session_id = "test"
    age = 22
    gender = "female"
    history = []
    scale_answers = {}

result = agent.run(MockRequest())
print(f"   结果: {result}")
print("   IntakeAgent 测试通过")

# 2. 测试 StructuringAgent
print("\n2. 测试 StructuringAgent...")
from app.agents.structuring_agent import StructuringAgent
agent = StructuringAgent()
result = agent.run({'follow_up_questions': [], 'summary': '情绪低落、失眠'})
print(f"   结果: {result}")
print("   StructuringAgent 测试通过")

# 3. 测试 ScaleAgent
print("\n3. 测试 ScaleAssessmentAgent...")
from app.agents.scale_agent import ScaleAssessmentAgent
agent = ScaleAssessmentAgent()
result = agent.run({'PHQ9': 16, 'GAD7': 11})
print(f"   结果: {result}")
print("   ScaleAssessmentAgent 测试通过")

# 4. 测试 MoodAngelsDiagnosisAgent
print("\n4. 测试 MoodAngelsDiagnosisAgent...")
from app.agents.moodangels_diagnosis_agent import MoodAngelsDiagnosisAgent
agent = MoodAngelsDiagnosisAgent()
result = agent.run({'symptoms': ['情绪低落']}, {'PHQ9': {'total': 16}})
print(f"   结果: {result}")
print("   MoodAngelsDiagnosisAgent 测试通过")

# 5. 测试 ModelVerificationAgent
print("\n5. 测试 ModelVerificationAgent...")
from app.agents.model_verification_agent import ModelVerificationAgent
agent = ModelVerificationAgent()
result = agent.run("测试文本", {})
print(f"   结果: {result}")
print("   ModelVerificationAgent 测试通过")

# 6. 测试 KnowledgeAgent
print("\n6. 测试 KnowledgeAgent...")
from app.agents.knowledge_agent import KnowledgeAgent
agent = KnowledgeAgent()
result = agent.run({'symptoms': ['情绪低落']}, {})
print(f"   结果: {result}")
print("   KnowledgeAgent 测试通过")

# 7. 测试 DifferentialDiagnosisAgent
print("\n7. 测试 DifferentialDiagnosisAgent...")
from app.agents.differential_agent import DifferentialDiagnosisAgent
agent = DifferentialDiagnosisAgent()
result = agent.run({'symptoms': ['情绪低落']}, {})
print(f"   结果: {result}")
print("   DifferentialDiagnosisAgent 测试通过")

# 8. 测试 RiskAssessmentAgent
print("\n8. 测试 RiskAssessmentAgent...")
from app.agents.risk_agent import RiskAssessmentAgent
agent = RiskAssessmentAgent()
result = agent.run("测试文本", {'symptoms': []}, {})
print(f"   结果: {result}")
print("   RiskAssessmentAgent 测试通过")

# 9. 测试 ValidatorAgent
print("\n9. 测试 ValidatorAgent...")
from app.agents.validator_agent import ValidatorAgent
agent = ValidatorAgent()
result = agent.run({'diagnosis': {}, 'risk': {}})
print(f"   结果: {result}")
print("   ValidatorAgent 测试通过")

# 10. 测试 ReportAgent
print("\n10. 测试 ReportAgent...")
from app.agents.report_agent import ReportAgent
agent = ReportAgent()
state = {
    'diagnosis': {},
    'risk': {},
    'validation': {},
    'knowledge': {},
    'differential': {},
    'model_verification': {},
    'scales': {},
    'structured': {},
    'intake': {},
    'agent_traces': [],
}
result = agent.run(state)
print(f"   结果: {result}")
print("   ReportAgent 测试通过")

print("\n" + "=" * 50)
print("所有 Agent 测试通过！")
print("=" * 50)
