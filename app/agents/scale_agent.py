from app.agents.base import BaseAgent


def level_phq9(score: int) -> str:
    if score >= 20:
        return 'severe'
    if score >= 15:
        return 'moderately_severe'
    if score >= 10:
        return 'moderate'
    if score >= 5:
        return 'mild'
    return 'minimal'


def level_gad7(score: int) -> str:
    if score >= 15:
        return 'severe'
    if score >= 10:
        return 'moderate'
    if score >= 5:
        return 'mild'
    return 'minimal'


def level_hamd(score: int) -> str:
    if score >= 24:
        return 'severe'
    if score >= 17:
        return 'moderate'
    if score >= 8:
        return 'mild'
    return 'normal'


def level_hama(score: int) -> str:
    if score >= 29:
        return 'severe'
    if score >= 21:
        return 'marked'
    if score >= 14:
        return 'definite'
    if score >= 7:
        return 'possible'
    return 'normal'


class ScaleAssessmentAgent(BaseAgent):
    name = 'ScaleAssessmentAgent'

    def run(self, scale_answers):
        phq = int(scale_answers.get('PHQ9', scale_answers.get('phq9', 0)) or 0)
        gad = int(scale_answers.get('GAD7', scale_answers.get('gad7', 0)) or 0)
        hamd = int(scale_answers.get('HAMD', scale_answers.get('hamd', 0)) or 0)
        hama = int(scale_answers.get('HAMA', scale_answers.get('hama', 0)) or 0)
        granular = []
        if phq >= 10:
            granular.append('PHQ-9达到中度及以上阈值，应重点追问兴趣减退、睡眠、精力、自责和自伤意念条目。')
        if gad >= 10:
            granular.append('GAD-7达到中度及以上阈值，应结合过度担忧、紧张、坐立不安和躯体化表现。')
        if hamd >= 17:
            granular.append('HAMD提示中度及以上抑郁症状，需由专业人员结合访谈评估。')
        if hama >= 14:
            granular.append('HAMA提示明确焦虑风险，需区分焦虑障碍、抑郁共病和躯体疾病因素。')
        if not granular:
            granular.append('量表信息不足或未达中度阈值，仍需结合临床访谈判断。')
        return {
            'PHQ9': {'score': phq, 'level': level_phq9(phq)},
            'GAD7': {'score': gad, 'level': level_gad7(gad)},
            'HAMD': {'score': hamd, 'level': level_hamd(hamd)},
            'HAMA': {'score': hama, 'level': level_hama(hama)},
            'granular_items': granular,
            'raw_scale_answers': scale_answers,
        }
