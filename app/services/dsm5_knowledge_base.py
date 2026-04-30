#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSM-5 知识检索引擎
基于三元组知识图谱 + 文本 RAG 双路检索
支持中英文混合检索
"""
import json
import re
from typing import List, Dict, Any
from pathlib import Path


class DSM5KnowledgeBase:
    """DSM-5 知识库 - 基于三元组的知识检索引擎"""

    # 中英文症状映射表
    SYMPTOM_MAP = {
        # 核心症状
        '抑郁': ['depress', 'depressive', 'depression', 'sad', 'mood'],
        '焦虑': ['anxiety', 'anxious', 'worry', 'nervous', 'panic'],
        '失眠': ['insomnia', 'sleep', 'wake up', 'sleeping'],
        '情绪低落': ['depressed mood', 'low mood', 'sad mood'],
        '兴趣减退': ['anhedonia', 'loss of interest', 'interest', 'pleasure'],
        '没兴趣': ['anhedonia', 'loss of interest', 'interest'],
        '精力': ['energy', 'fatigue', 'tired'],
        '疲劳': ['fatigue', 'tired', 'exhausted'],
        '自责': ['guilt', 'guilty', 'blame', 'worthless'],
        '自杀': ['suicide', 'suicidal', 'self-harm', 'self harm', 'death'],
        '自伤': ['self-harm', 'self harm', 'suicidal'],
        '活着没意思': ['suicide', 'suicidal', 'worthless', 'hopeless'],
        '不想活': ['suicide', 'suicidal', 'hopeless'],

        # 双相相关
        '躁狂': ['mania', 'manic', 'elevated mood', 'expansive'],
        '轻躁狂': ['hypomania', 'hypomanic'],
        '双相': ['bipolar', 'manic-depressive', 'manic depressive'],
        '精力旺盛': ['increased energy', 'energy', 'decreased sleep'],
        '话多': ['talkative', 'pressured speech', 'speech'],
        '冲动': ['impulsive', 'impulsivity', 'risky behavior'],

        # 精神病性
        '幻觉': ['hallucination', 'hallucinations', 'perceptual'],
        '妄想': ['delusion', 'delusions'],
        '被害': ['paranoid', 'persecutory', 'suspicious'],
        '精神病': ['psychotic', 'psychosis'],

        # 认知
        '注意力': ['concentration', 'attention', 'focus'],
        '记忆': ['memory', 'forget', 'recall'],
        '认知': ['cognitive', 'cognition'],

        # 躯体
        '食欲': ['appetite', 'weight', 'eating'],
        '体重': ['weight', 'appetite'],
        '心慌': ['palpitations', 'heart', 'racing'],
        '紧张': ['tension', 'tense', 'restless'],
        '坐立不安': ['restless', 'agitation', 'psychomotor'],

        # 疾病名称
        '抑郁障碍': ['depressive disorder', 'major depression', 'mdd'],
        '焦虑障碍': ['anxiety disorder', 'gad', 'generalized anxiety'],
        '双相障碍': ['bipolar disorder', 'bipolar i', 'bipolar ii'],
        '精神分裂': ['schizophrenia', 'schizophreniform', 'schizoaffective'],
    }

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.triples = []
        self.text_content = ""
        self.symptom_index = {}
        self.disorder_index = {}
        self._load_knowledge()

    def _load_knowledge(self):
        """加载知识库 - 完整加载所有三元组"""
        base_path = Path(__file__).parent.parent.parent / 'data' / 'knowledge'

        # 加载三元组（完整加载，不限制数量）
        triples_path = base_path / 'dsm5_triples_optimized.json'
        if triples_path.exists():
            with open(triples_path, 'r', encoding='utf-8') as f:
                self.triples = json.load(f)
            print(f'加载了 {len(self.triples)} 条 DSM-5 三元组')
            self._build_index()

        # 加载文本（只加载前 100KB 做演示，完整版本可扩展）
        text_path = base_path / 'DSM-5-TR_djvu.txt'
        if text_path.exists():
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.text_content = f.read(100 * 1024)

    def _build_index(self):
        """构建关键词索引 - 改进版"""
        for idx, triple in enumerate(self.triples):
            head = triple.get('head_entity', '').lower()
            tail = triple.get('tail_entity', '').lower()
            sentence = triple.get('sentence', '').lower()

            # 索引所有英文单词
            all_text = f"{head} {tail} {sentence}"

            # 提取英文单词（2个字母以上）
            for keyword in re.findall(r'\b[a-zA-Z]{2,}\b', all_text):
                keyword = keyword.lower()
                if keyword not in self.symptom_index:
                    self.symptom_index[keyword] = []
                if idx not in self.symptom_index[keyword]:
                    self.symptom_index[keyword].append(idx)

            # 索引疾病名称
            if 'disorder' in tail or 'disease' in tail or 'condition' in tail:
                if tail not in self.disorder_index:
                    self.disorder_index[tail] = []
                if idx not in self.disorder_index[tail]:
                    self.disorder_index[tail].append(idx)

    def _translate_symptom(self, symptom) -> List[str]:
        """将中文症状翻译为相关的英文关键词列表"""
        # 处理字典类型的症状（来自结构化输出）
        if isinstance(symptom, dict):
            symptom = str(symptom.get('name', '') or symptom.get('text', '') or '')
        # 处理列表类型
        if isinstance(symptom, list):
            symptom = ' '.join(str(s) for s in symptom)
        
        symptom_lower = str(symptom).lower()
        keywords = []

        # 查找映射表
        for cn_term, en_terms in self.SYMPTOM_MAP.items():
            if cn_term in symptom_lower or symptom_lower in cn_term:
                keywords.extend(en_terms)

        # 如果没有找到映射，尝试直接使用中文（如果有）
        if not keywords and len(re.findall(r'[\u4e00-\u9fff]', symptom)) > 0:
            # 这是纯中文，没有映射，使用通用关键词
            pass

        # 去重
        return list(set(keywords))

    def search_by_symptoms(self, symptoms, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        根据症状列表检索相关知识（支持中英文）

        Args:
            symptoms: 症状列表，如 ['情绪低落', '失眠', '焦虑']
            top_k: 返回结果数量
        """
        if not symptoms:
            return []
        
        # 标准化为字符串列表
        if isinstance(symptoms, str):
            symptoms = [symptoms]
        symptom_strings = []
        for s in symptoms:
            if isinstance(s, dict):
                # 处理字典格式
                symptom_str = str(s.get('name', '') or s.get('text', '') or s.get('symptom', ''))
                if symptom_str:
                    symptom_strings.append(symptom_str)
            elif isinstance(s, str):
                symptom_strings.append(s)
            elif s is not None:
                symptom_strings.append(str(s))

        matched_indices = {}  # idx -> 匹配次数（用于排序）
        matched_triples = {}

        for symptom in symptom_strings:
            # 获取英文关键词
            en_keywords = self._translate_symptom(symptom)

            # 如果有英文关键词，用英文搜索
            if en_keywords:
                for keyword in en_keywords:
                    if keyword in self.symptom_index:
                        for idx in self.symptom_index[keyword]:
                            matched_indices[idx] = matched_indices.get(idx, 0) + 1
                            matched_triples[idx] = self.triples[idx]
            else:
                # 尝试直接用原文搜索
                symptom_lower = symptom.lower()
                for keyword, indices in self.symptom_index.items():
                    if symptom_lower in keyword or keyword in symptom_lower:
                        for idx in indices:
                            matched_indices[idx] = matched_indices.get(idx, 0) + 1
                            matched_triples[idx] = self.triples[idx]

        # 按匹配次数和置信度排序
        results = []
        for idx, match_count in matched_indices.items():
            triple = matched_triples[idx]
            results.append({
                'head_entity': triple.get('head_entity'),
                'relation': triple.get('relation'),
                'tail_entity': triple.get('tail_entity'),
                'sentence': triple.get('sentence'),
                'confidence': triple.get('confidence_score', 0.5),
                'match_count': match_count,
            })

        # 排序：先按匹配次数，再按置信度
        results.sort(key=lambda x: (x['match_count'], x['confidence']), reverse=True)

        return results[:top_k]

    def search_by_disorder(self, disorder_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        根据疾病名称检索相关知识（支持中英文）

        Args:
            disorder_name: 疾病名称，如 '抑郁障碍'
            top_k: 返回结果数量
        """
        # 获取英文关键词
        en_keywords = self._translate_symptom(disorder_name)

        matched_indices = {}

        # 用英文关键词搜索
        for keyword in en_keywords:
            for name, indices in self.disorder_index.items():
                if keyword in name.lower():
                    for idx in indices:
                        matched_indices[idx] = matched_indices.get(idx, 0) + 1

        # 如果没有结果，尝试直接搜索
        if not matched_indices:
            disorder_lower = disorder_name.lower()
            for name, indices in self.disorder_index.items():
                if disorder_lower in name.lower():
                    for idx in indices:
                        matched_indices[idx] = matched_indices.get(idx, 0) + 1

        results = []
        for idx, match_count in matched_indices.items():
            triple = self.triples[idx]
            results.append({
                'head_entity': triple.get('head_entity'),
                'relation': triple.get('relation'),
                'tail_entity': triple.get('tail_entity'),
                'sentence': triple.get('sentence'),
                'confidence': triple.get('confidence_score', 0.5),
                'match_count': match_count,
            })

        results.sort(key=lambda x: (x['match_count'], x['confidence']), reverse=True)
        return results[:top_k]

    def get_diagnostic_criteria(self, disorder_name: str) -> str:
        """
        从文本中检索诊断标准（简化版）
        """
        disorder_lower = disorder_name.lower()
        lines = self.text_content.split('\n')

        relevant_lines = []
        for i, line in enumerate(lines):
            if disorder_lower in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 10)
                relevant_lines.extend(lines[start:end])
                if len(relevant_lines) > 50:
                    break

        return '\n'.join(relevant_lines) if relevant_lines else ""

    def get_knowledge_summary(self, symptoms: List[str], hypotheses: List[str]) -> Dict[str, Any]:
        """
        获取完整的知识增强摘要

        Args:
            symptoms: 症状列表
            hypotheses: 诊断假设列表
        """
        # 1. 基于症状检索知识
        symptom_knowledge = self.search_by_symptoms(symptoms, top_k=3)

        # 2. 基于诊断假设检索知识
        disorder_knowledge = []
        for hyp in hypotheses:
            disorder_knowledge.extend(self.search_by_disorder(hyp, top_k=2))

        # 3. 去重
        seen = set()
        unique_knowledge = []
        for item in symptom_knowledge + disorder_knowledge:
            key = item.get('sentence', '')
            if key and key not in seen:
                seen.add(key)
                unique_knowledge.append(item)

        # 4. 生成规则提示
        rules_applied = self._generate_rules(symptoms, hypotheses)

        return {
            'rag_evidence': [item.get('sentence', '') for item in unique_knowledge[:5] if item.get('sentence')],
            'kg_nodes': unique_knowledge[:3],
            'rules_applied': rules_applied,
            'knowledge_source': 'DSM-5-TR 知识图谱',
        }

    def _generate_rules(self, symptoms: List[str], hypotheses: List[str]) -> List[str]:
        """生成诊断规则提示"""
        rules = []
        symptoms_text = ' '.join(symptoms).lower()
        hypotheses_text = ' '.join(hypotheses).lower()

        # 基础规则
        rules.append('non-diagnostic-output：仅输出辅助筛查建议，不得确诊')
        rules.append('risk-first：高风险症状优先处理')

        # 抑郁相关规则
        if '抑郁' in hypotheses_text or 'depress' in hypotheses_text:
            rules.append('抑郁评估应关注：持续心境低落、兴趣减退、睡眠/食欲改变、精力下降、自责、自伤意念及功能损害')

        # 双相相关规则
        if '双相' in hypotheses_text or 'bipolar' in hypotheses_text:
            rules.append('出现抑郁表现时必须追问躁狂/轻躁狂史，避免双相抑郁被误判为单相抑郁')

        # 焦虑相关规则
        if '焦虑' in hypotheses_text or 'anxiety' in hypotheses_text or '焦虑' in symptoms_text:
            rules.append('焦虑需与抑郁共病、躯体疾病、物质/药物因素鉴别')

        # 精神病性症状规则
        if '精神病' in hypotheses_text or 'psychotic' in hypotheses_text or '幻觉' in symptoms_text or '妄想' in symptoms_text:
            rules.append('幻觉、妄想、被害感等精神病性症状需要优先建议线下专业评估')

        # 自杀风险规则
        if '自杀' in symptoms_text or '不想活' in symptoms_text or '活着没意思' in symptoms_text:
            rules.append('存在自伤/自杀意念时，必须强制建议立即就医或联系危机干预热线')

        return rules

    @property
    def stats(self) -> Dict[str, int]:
        """知识库统计信息"""
        return {
            'total_triples': len(self.triples),
            'indexed_symptoms': len(self.symptom_index),
            'indexed_disorders': len(self.disorder_index),
        }


# 全局单例
_dsm5_kb = None


def get_dsm5_knowledge_base() -> DSM5KnowledgeBase:
    """获取 DSM-5 知识库单例"""
    global _dsm5_kb
    if _dsm5_kb is None:
        _dsm5_kb = DSM5KnowledgeBase()
    return _dsm5_kb


if __name__ == '__main__':
    # 测试
    kb = get_dsm5_knowledge_base()
    print('知识库统计:', kb.stats)

    print('\n测试症状检索:')
    results = kb.search_by_symptoms(['抑郁', '失眠', '焦虑'])
    for r in results[:3]:
        print(f'  - {r["sentence"]}')

    print('\n测试疾病检索:')
    results = kb.search_by_disorder('抑郁障碍')
    for r in results[:3]:
        print(f'  - {r["sentence"]}')
