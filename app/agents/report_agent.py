from app.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    name = 'ReportAgent'

    def run(self, state):
        diagnosis = state.get('validation', {}).get('sanitized_diagnosis') or state.get('diagnosis', {}).get('hypotheses', [])
        risk = state.get('risk', {})
        knowledge = state.get('knowledge', {})
        differential = state.get('differential', {})
        scales = state.get('scales', {})
        evidence = []
        evidence.extend(state.get('diagnosis', {}).get('evidence', []))
        evidence.extend(scales.get('granular_items', []))
        evidence.extend(knowledge.get('rag_evidence', []))
        evidence.extend(differential.get('differential_items', []))
        recommendations = ['建议由精神科/心理科专业人员进一步评估。', '建议补充既往发作史、家族史、用药史、功能损害和持续时间。']
        if risk.get('risk_level') == 'high':
            recommendations.insert(0, '当前存在高危风险提示，请优先进行安全干预和线下就医。')
        return {
            'suspected_diagnosis': diagnosis,
            'risk_level': risk.get('risk_level', 'unknown'),
            'risk_types': risk.get('risk_types', []),
            'evidence_chain': list(dict.fromkeys([str(x) for x in evidence if x])),
            'recommendations': recommendations,
            'safety_message': state.get('validation', {}).get('safety_message', ''),
            'structured_report': {
                'intake': state.get('intake', {}),
                'case': state.get('structured', {}),
                'scales': scales,
                'moodangels': state.get('diagnosis', {}),
                'external_models': state.get('model_verification', {}),
                'knowledge': knowledge,
                'differential': differential,
                'risk': risk,
                'validation': state.get('validation', {}),
            },
        }
