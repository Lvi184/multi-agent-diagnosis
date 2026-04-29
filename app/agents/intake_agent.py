from app.agents.base import BaseAgent
from app.services.rules import HIGH_RISK, hits


class IntakeAgent(BaseAgent):
    name = 'IntakeAgent'

    def run(self, request):
        text = ' '.join((request.text or '').split())
        history = request.history or []
        risk_hits = hits(text, HIGH_RISK)
        fallback = {
            'raw_text': text,
            'conversation_history': history,
            'chief_complaint': text[:160],
            'present_illness': '需继续追问起病时间、诱因、持续时间、功能损害。',
            'past_history': '未提供' if not history else '；'.join(history[-3:]),
            'medication_history': '未提供',
            'suicide_self_harm_screening': 'positive' if risk_hits else 'negative',
            'risk_clues': risk_hits,
            'followup_questions': [
                '这些症状持续了多久？是否每天都出现？',
                '睡眠、食欲、学习/工作功能是否受到影响？',
                '是否有伤害自己或结束生命的具体计划？',
                '既往是否有躁狂/轻躁狂、精神科就诊或用药史？',
            ],
            'need_followup': len(text) < 30 or bool(risk_hits),
        }
        return self.llm.json_chat(
            '你是精神健康辅助筛查系统中的 Intake Agent，负责多轮问答入口、主诉、现病史、既往史、用药史和自伤自杀风险初筛。不得输出确诊。',
            f'患者输入：{text}\n历史对话：{history}\n请输出字段：raw_text, chief_complaint, present_illness, past_history, medication_history, suicide_self_harm_screening, risk_clues, followup_questions, need_followup。',
            fallback,
        )
