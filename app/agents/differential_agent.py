from app.agents.base import BaseAgent


class DifferentialDiagnosisAgent(BaseAgent):
    name = 'DifferentialDiagnosisAgent'

    def run(self, structured, diagnosis):
        hyps = diagnosis.get('hypotheses', [])
        diffs = []
        if any('抑郁' in h for h in hyps):
            diffs.append('抑郁 vs 双相：必须追问既往躁狂/轻躁狂发作、睡眠需求减少、精力增多和冲动行为。')
            diffs.append('抑郁 vs 焦虑：区分核心低落/兴趣减退与持续过度担忧。')
        if any('焦虑' in h for h in hyps):
            diffs.append('焦虑 vs 躯体疾病/药物因素：需排除甲状腺、心血管、咖啡因或药物影响。')
        diffs.append('心境障碍 vs 精神分裂谱系：需评估幻觉、妄想、思维紊乱是否独立于心境发作存在。')
        fallback = {'differential_items': diffs, 'missing_information': ['家族史', '既往发作史', '用药史', '功能损害', '持续时间']}
        return self.llm.json_chat(
            '你是 Differential Diagnosis Agent，负责抑郁/双相/焦虑/精神分裂谱系鉴别诊断。不得确诊。',
            f'结构化病历：{structured}\n诊断假设：{hyps}\n请输出 differential_items 和 missing_information。',
            fallback,
        )
