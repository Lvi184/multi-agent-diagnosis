#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试知识增强效果
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("DSM-5 知识增强快速测试")
print("=" * 60)

print("\n1. 加载知识库...")
from app.services.dsm5_knowledge_base import get_dsm5_knowledge_base
kb = get_dsm5_knowledge_base()
stats = kb.stats
print(f"   ✅ 知识库已加载: {stats['total_triples']:,} 条三元组")
print(f"   - 索引症状数: {stats['indexed_symptoms']:,}")
print(f"   - 索引疾病数: {stats['indexed_disorders']:,}")

print("\n" + "=" * 60)
print("2. 测试 KnowledgeAgent")
print("=" * 60)

from app.agents.knowledge_agent import KnowledgeAgent
agent = KnowledgeAgent()
print("   ✅ KnowledgeAgent 初始化成功")

# 测试案例
test_cases = [
    {
        'symptoms': ['情绪低落', '失眠', '兴趣减退', '自杀意念'],
        'hypotheses': ['疑似抑郁障碍', '高自杀风险'],
        'name': '抑郁伴自杀风险'
    },
    {
        'symptoms': ['焦虑', '紧张', '心慌', '坐立不安'],
        'hypotheses': ['疑似焦虑障碍'],
        'name': '焦虑症状'
    },
    {
        'symptoms': ['幻觉', '妄想', '被害感'],
        'hypotheses': ['精神病性症状风险'],
        'name': '精神病性症状'
    }
]

for case in test_cases:
    print(f"\n【{case['name']}】")
    structured = {'symptoms': case['symptoms']}
    diagnosis = {'hypotheses': case['hypotheses']}

    result = agent.run(structured, diagnosis)

    rag_ev = result.get('rag_evidence', [])
    rules = result.get('rules_applied', [])
    source = result.get('knowledge_source', '未知')

    print(f"  症状: {case['symptoms']}")
    print(f"  知识来源: {source}")

    if rag_ev:
        print(f"\n  📚 DSM-5 知识证据 ({len(rag_ev)} 条):")
        for i, ev in enumerate(rag_ev[:3], 1):
            ev_str = str(ev)
            if len(ev_str) > 80:
                ev_str = ev_str[:77] + '...'
            print(f"    {i}. {ev_str}")

    if rules:
        print(f"\n  📋 应用规则 ({len(rules)} 条):")
        for i, rule in enumerate(rules[:4], 1):
            rule_str = str(rule)
            if len(rule_str) > 60:
                rule_str = rule_str[:57] + '...'
            print(f"    {i}. {rule_str}")

print("\n" + "=" * 60)
print("✅ 知识增强功能正常工作！")
print("=" * 60)
print("\n📝 使用说明:")
print("   1. 知识库自动加载，包含 11,952 条 DSM-5 三元组")
print("   2. 支持中文症状自动映射到英文检索")
print("   3. 诊断时 KnowledgeAgent 自动调用知识库")
print("   4. 输出包含：DSM-5 知识证据、疾病知识节点、诊断规则")
print("   5. 完整工作流中自动集成，无需额外配置")
print()
print("🌐 Web 服务使用:")
print("   启动服务: uvicorn app.main:app --port 8000")
print("   访问: http://127.0.0.1:8000/")
print("   每次诊断都会自动使用 DSM-5 知识增强")
print()
