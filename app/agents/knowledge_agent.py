from app.agents.base import BaseAgent
from app.services.dsm5_knowledge_base import get_dsm5_knowledge_base


class KnowledgeAgent(BaseAgent):
    """
    知识增强 Agent - 基于 DSM-5 知识图谱的诊断支持

    功能:
    - 基于症状检索 DSM-5 相关知识
    - 基于诊断假设检索疾病诊断标准
    - 应用诊断规则和禁忌
    - 提供知识图谱证据链
    """

    name = 'KnowledgeAgent'

    def __init__(self):
        super().__init__()
        try:
            self.kb = get_dsm5_knowledge_base()
        except Exception as e:
            print(f'知识库加载失败: {e}，使用回退模式')
            self.kb = None

    def run(self, structured, diagnosis):
        hyps = diagnosis.get('hypotheses', [])
        symptoms = structured.get('symptoms', [])

        # 如果知识库可用，使用真实知识检索
        if self.kb:
            kb_result = self.kb.get_knowledge_summary(symptoms, hyps)
            rag_evidence = kb_result.get('rag_evidence', [])
            kg_nodes = kb_result.get('kg_nodes', [])
            rules_applied = kb_result.get('rules_applied', [])

            # 如果检索到的知识不够，补充默认规则
            if not rag_evidence:
                rag_evidence = self._get_fallback_evidence(hyps)

            # 补充默认规则
            if len(rules_applied) < 2:
                rules_applied.extend(['non-diagnostic-output', 'risk-first'])
        else:
            # 知识库不可用，使用回退模式
            rag_evidence = self._get_fallback_evidence(hyps)
            kg_nodes = hyps
            rules_applied = ['non-diagnostic-output', 'risk-first', 'differential-required']

        fallback = {
            'rag_evidence': rag_evidence,
            'kg_nodes': kg_nodes,
            'rules_applied': rules_applied,
            'knowledge_source': 'DSM-5-TR 知识图谱' if self.kb else '内置规则库',
            'kb_stats': self.kb.stats if self.kb else None,
        }

        return self.llm.json_chat(
            '你是 Knowledge Agent，负责 DSM-5/ICD RAG、精神疾病知识图谱查询和规则库强约束。不得确诊。',
            f'结构化病历：{structured}\n诊断节点输出：{diagnosis}\n请输出 rag_evidence, kg_nodes, rules_applied。',
            fallback,
        )

    def _get_fallback_evidence(self, hyps):
        """回退证据 - 当知识库不可用时使用"""
        ev = []
        hyps_text = ' '.join(hyps).lower() if hyps else ''

        if '抑郁' in hyps_text or 'depress' in hyps_text:
            ev.append('DSM-5 知识提示：抑郁评估应关注持续心境低落、兴趣减退、睡眠/食欲改变、精力下降、自责、自伤意念及功能损害。')
        if '双相' in hyps_text or 'bipolar' in hyps_text:
            ev.append('DSM-5 规则提示：出现抑郁表现时必须追问躁狂/轻躁狂史，避免双相抑郁被误判为单相抑郁。')
        if '焦虑' in hyps_text or 'anxiety' in hyps_text:
            ev.append('DSM-5 知识提示：焦虑需与抑郁共病、躯体疾病、物质/药物因素鉴别。')
        if '精神病' in hyps_text or 'psychotic' in hyps_text:
            ev.append('DSM-5 风险提示：幻觉、妄想、被害感等精神病性症状需要优先建议线下专业评估。')

        if not ev:
            ev.append('DSM-5 知识提示：当前信息不足，建议继续采集持续时间、严重程度、功能损害、既往史和用药史。')

        return ev
