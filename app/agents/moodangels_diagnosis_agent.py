from app.agents.base import BaseAgent


class MoodAngelsDiagnosisAgent(BaseAgent):
    """融合版 MoodAngels 核心诊断节点。

    原 MoodAngels 公开代码不完整且依赖私有数据/embedding/工具函数。本类不再要求保留原文件格式，
    而是把其公开思想直接融合进当前系统：
    - Angel.R: 不参考历史案例，仅依据结构化病历、量表与DSM线索判断；
    - Angel.D: 展示相似病例/相似量表信号；
    - Angel.C: 分析当前个案与相似案例异同；
    - Debate Agents: 正反辩论；
    - Judge Agent: 汇总裁决，输出“疑似/风险”而非确诊。
    """

    name = 'MoodAngelsDiagnosisAgent'

    def run(self, structured, scales):
        fallback = self._rule_based_moodangels(structured, scales)
        user = f"""
结构化病历：{structured}
量表评估：{scales}
请模拟 MoodAngels 多智能体诊断流程，输出 JSON：
{{
  "hypotheses": ["疑似诊断或风险"],
  "angel_r": {{"agent":"Angel.R", "view":"...", "hypotheses":[]}},
  "angel_d": {{"agent":"Angel.D", "similar_case_signal":[]}},
  "angel_c": {{"agent":"Angel.C", "similarities":"...", "differences":"..."}},
  "debate": {{"positive":"...", "negative":"..."}},
  "judge": {{"decision":[], "confidence":0.0, "reason":"..."}},
  "evidence": []
}}
注意：只能输出疑似诊断、风险提示和就医建议，不得输出医学确诊。
"""
        return self.llm.json_chat(
            '你是 MoodAngels Diagnosis Agents 的融合实现，负责 Angel.R、Angel.D、Angel.C、Debate Agents 和 Judge Agent 的核心诊断推理。',
            user,
            fallback,
        )

    def _rule_based_moodangels(self, structured, scales):
        symptoms = structured.get('symptoms', [])
        phq = scales.get('PHQ9', {}).get('score', 0)
        gad = scales.get('GAD7', {}).get('score', 0)
        hamd = scales.get('HAMD', {}).get('score', 0)
        hama = scales.get('HAMA', {}).get('score', 0)
        hyps = []
        if phq >= 10 or hamd >= 17 or any(s in symptoms for s in ['情绪低落', '没兴趣', '兴趣减退', '绝望']):
            hyps.append('疑似抑郁障碍相关风险')
        if gad >= 10 or hama >= 14 or any(s in symptoms for s in ['焦虑', '担心', '紧张', '心慌']):
            hyps.append('焦虑症状显著')
        if any(s in symptoms for s in ['几天不睡', '精力特别旺盛', '话特别多', '冲动消费']):
            hyps.append('疑似双相相关风险')
        if any(s in symptoms for s in ['幻听', '幻觉', '被害', '有人监视', '妄想']):
            hyps.append('精神病性症状风险')
        if not hyps:
            hyps.append('当前信息不足，需进一步评估')

        evidence = []
        evidence += [f'症状线索：{x}' for x in symptoms]
        evidence += scales.get('granular_items', [])
        return {
            'hypotheses': hyps,
            'angel_r': {
                'agent': 'Angel.R',
                'view': '不参考历史案例，仅基于结构化病历、量表和DSM/ICD线索形成初步假设。',
                'hypotheses': hyps,
            },
            'angel_d': {
                'agent': 'Angel.D',
                'view': '在缺少原始私有病例库时，使用症状和量表相似信号替代相似病例展示。',
                'similar_case_signal': symptoms + scales.get('granular_items', []),
            },
            'angel_c': {
                'agent': 'Angel.C',
                'similarities': '当前个案与心境障碍/焦虑相关表现存在症状或量表层面的相似信号。',
                'differences': '仍需追问躁狂史、精神病性症状、物质/药物因素、躯体疾病和功能损害。',
            },
            'debate': {
                'positive': '支持方：症状和量表达到风险筛查阈值，建议进一步精神科/心理科评估。',
                'negative': '反对方：信息来自自述和筛查量表，缺乏完整临床访谈，不能确诊。',
            },
            'judge': {
                'decision': hyps,
                'confidence': 0.76 if len(hyps) > 1 else 0.58,
                'reason': '综合 Angel.R/D/C 和辩论结果，仅输出辅助筛查层面的疑似风险。',
            },
            'evidence': evidence,
            'source': 'integrated_legacy_moodangels_engine',
        }
