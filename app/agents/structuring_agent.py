from app.agents.base import BaseAgent
from app.services.rules import DEPRESSIVE, ANXIETY, MANIA, PSYCHOSIS, HIGH_RISK, hits


class StructuringAgent(BaseAgent):
    name = 'StructuringAgent'

    def run(self, intake):
        text = intake.get('raw_text', '')
        symptom_hits = list(dict.fromkeys(hits(text, DEPRESSIVE + ANXIETY + MANIA + PSYCHOSIS + HIGH_RISK)))
        duration = '未明确'
        for key in ['两个月', '2个月', '三个月', '3个月', '一周', '1周', '半年', '一年']:
            if key in text:
                duration = key
                break
        severity = 'high' if hits(text, HIGH_RISK) else ('moderate' if len(symptom_hits) >= 3 else 'uncertain')
        fallback = {
            'symptoms': symptom_hits,
            'timeline': duration,
            'severity': severity,
            'functional_impairment': '需进一步追问',
            'structured_case': {
                '主诉': intake.get('chief_complaint', ''),
                '现病史': intake.get('present_illness', ''),
                '既往史': intake.get('past_history', '未提供'),
                '用药史': intake.get('medication_history', '未提供'),
                '风险线索': intake.get('risk_clues', []),
            },
            'scale_answer_notes': '若前端传入PHQ9/GAD7/HAMD/HAMA总分则进入量表节点；若传入题目级答案可扩展逐题评分。',
        }
        return self.llm.json_chat(
            '你是 Structuring Agent，负责把患者自然语言和采集信息转为结构化病历，抽取症状、时间线、严重程度和量表答案整理提示。不得输出确诊。',
            f'采集结果：{intake}\n请输出 symptoms, timeline, severity, functional_impairment, structured_case, scale_answer_notes。',
            fallback,
        )
