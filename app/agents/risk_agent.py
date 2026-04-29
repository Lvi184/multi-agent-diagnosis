from app.agents.base import BaseAgent
from app.services.rules import HIGH_RISK, MANIA, PSYCHOSIS, hits


class RiskAssessmentAgent(BaseAgent):
    name = 'RiskAssessmentAgent'

    def run(self, text, structured, model_verification):
        suicide_hits = hits(text, HIGH_RISK)
        mania_hits = hits(text, MANIA)
        psychosis_hits = hits(text, PSYCHOSIS)
        risk_types = []
        if suicide_hits:
            risk_types.append('suicide_or_self_harm')
        if mania_hits:
            risk_types.append('mania')
        if psychosis_hits:
            risk_types.append('psychotic_symptoms')
        mentalbert_label = model_verification.get('mentalbert', {}).get('label', 'low')
        if mentalbert_label == 'high' and 'suicide_or_self_harm' not in risk_types:
            risk_types.append('suicide_or_self_harm')
        if 'suicide_or_self_harm' in risk_types:
            level = 'high'
        elif risk_types:
            level = 'moderate'
        else:
            level = 'low'
        fallback = {
            'risk_level': level,
            'risk_types': risk_types,
            'matched_rules': {
                'suicide_self_harm': suicide_hits,
                'mania': mania_hits,
                'psychosis': psychosis_hits,
            },
            'action': 'urgent_intervention' if level == 'high' else 'routine_followup',
        }
        return self.llm.json_chat(
            '你是 Risk Assessment Agent，负责自杀、自伤、躁狂、精神病性症状风险评估。高危风险必须优先处理，但不得确诊。',
            f'文本：{text}\n结构化病历：{structured}\n外部验证：{model_verification}\n请输出 risk_level, risk_types, matched_rules, action。',
            fallback,
        )
