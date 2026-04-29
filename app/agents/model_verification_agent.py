from app.agents.base import BaseAgent
from app.services.rules import HIGH_RISK, MANIA, PSYCHOSIS, hits


class ModelVerificationAgent(BaseAgent):
    name = 'ModelVerificationAgent'

    def run(self, text, diagnosis):
        hr = hits(text, HIGH_RISK)
        neuro = hits(text, MANIA + PSYCHOSIS)
        score = min(0.99, 0.25 + 0.25 * len(hr)) if hr else 0.12
        fallback = {
            'mentalbert': {
                'model': 'MentalBERT-compatible-risk-adapter',
                'risk_score': score,
                'label': 'high' if score >= 0.5 else 'low',
                'evidence': hr,
            },
            'neurocheck': {
                'model': 'NeuroCheck-compatible-neuro-cognitive-adapter',
                'cognitive_neuro_risk': 'possible' if neuro else 'low',
                'evidence': neuro,
            },
            'consistency': 'external signals reviewed',
            'summary': '外部模型层当前以可替换适配器形式实现，可后续替换为真实 MentalBERT / NeuroCheck 推理服务。',
        }
        return self.llm.json_chat(
            '你是 Model Verification Agent，负责调用/模拟 MentalBERT 与 NeuroCheck，并汇总外部模型风险信号。不得确诊。',
            f'患者文本：{text}\nMoodAngels输出：{diagnosis}\n请输出 mentalbert, neurocheck, consistency, summary。',
            fallback,
        )
