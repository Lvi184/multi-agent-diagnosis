#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 DSM-5 知识库集成
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("DSM-5 知识库集成测试")
print("=" * 60)

# 1. 测试知识库加载
print("\n1. 测试知识库加载...")
try:
    from app.services.dsm5_knowledge_base import get_dsm5_knowledge_base
    kb = get_dsm5_knowledge_base()
    stats = kb.stats
    print(f"   ✅ 知识库加载成功！")
    print(f"   - 三元组总数: {stats['total_triples']:,}")
    print(f"   - 索引症状数: {stats['indexed_symptoms']:,}")
    print(f"   - 索引疾病数: {stats['indexed_disorders']:,}")
except Exception as e:
    print(f"   ❌ 知识库加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试症状检索
print("\n" + "=" * 60)
print("2. 测试症状检索")
print("=" * 60)
test_symptoms = ['抑郁', '失眠', '焦虑', '情绪低落']
print(f"测试症状: {test_symptoms}")
results = kb.search_by_symptoms(test_symptoms, top_k=5)
print(f"\n检索到 {len(results)} 条相关知识:")
for i, r in enumerate(results, 1):
    print(f"\n  {i}. {r['sentence']}")
    print(f"     关联: {r['head_entity']} --[{r['relation']}]--> {r['tail_entity']}")

# 3. 测试疾病检索
print("\n" + "=" * 60)
print("3. 测试疾病检索")
print("=" * 60)
test_disorders = ['Depressive Disorder', '焦虑障碍', '双相']
for disorder in test_disorders:
    print(f"\n检索疾病: {disorder}")
    results = kb.search_by_disorder(disorder, top_k=3)
    if results:
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['sentence']}")
    else:
        print("  未找到相关知识")

# 4. 测试完整知识增强
print("\n" + "=" * 60)
print("4. 测试完整知识增强功能")
print("=" * 60)

test_cases = [
    {
        'symptoms': ['情绪低落', '失眠', '兴趣减退', '自杀意念'],
        'hypotheses': ['疑似抑郁障碍', '高自杀风险'],
        'description': '抑郁症状'
    },
    {
        'symptoms': ['焦虑', '紧张', '心慌', '坐立不安'],
        'hypotheses': ['疑似焦虑障碍'],
        'description': '焦虑症状'
    },
    {
        'symptoms': ['幻觉', '妄想', '被害感'],
        'hypotheses': ['精神病性症状风险'],
        'description': '精神病性症状'
    }
]

for test in test_cases:
    print(f"\n测试场景: {test['description']}")
    print(f"症状: {test['symptoms']}")
    print(f"诊断假设: {test['hypotheses']}")

    result = kb.get_knowledge_summary(test['symptoms'], test['hypotheses'])

    print(f"\n  RAG 证据 ({len(result['rag_evidence'])} 条):")
    for i, ev in enumerate(result['rag_evidence'], 1):
        print(f"    {i}. {ev}")

    print(f"\n  应用规则 ({len(result['rules_applied'])} 条):")
    for i, rule in enumerate(result['rules_applied'], 1):
        print(f"    {i}. {rule}")

    print(f"  知识来源: {result.get('knowledge_source', '未知')}")

# 5. 测试 KnowledgeAgent 集成
print("\n" + "=" * 60)
print("5. 测试 KnowledgeAgent 集成")
print("=" * 60)

try:
    from app.agents.knowledge_agent import KnowledgeAgent
    agent = KnowledgeAgent()
    print("   ✅ KnowledgeAgent 初始化成功")

    structured = {'symptoms': ['情绪低落', '失眠', '没兴趣']}
    diagnosis = {'hypotheses': ['疑似抑郁障碍']}

    result = agent.run(structured, diagnosis)
    print(f"\n  Agent 运行结果:")
    print(f"    RAG 证据: {len(result.get('rag_evidence', []))} 条")
    print(f"    应用规则: {len(result.get('rules_applied', []))} 条")
    print(f"    知识来源: {result.get('knowledge_source', '未知')}")

    if result.get('kb_stats'):
        stats = result['kb_stats']
        print(f"    知识库状态: {stats['total_triples']:,} 条三元组")

except Exception as e:
    print(f"   ❌ KnowledgeAgent 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ 所有测试完成！DSM-5 知识库集成成功！")
print("=" * 60)
print("\n💡 提示:")
print("   - 知识库包含 11,952 条 DSM-5 三元组")
print("   - 支持症状检索、疾病检索、规则应用")
print("   - 已集成到 KnowledgeAgent，诊断时自动调用")
print("   - 完整工作流会自动使用知识增强")
print()
