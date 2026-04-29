from app.agents.base import BaseAgent


class ValidatorAgent(BaseAgent):
    name = 'ValidatorAgent'

    def run(self, report_parts):
        risk = report_parts.get('risk', {})
        messages = ['本系统输出为精神健康辅助筛查建议，不构成医学确诊。']
        passed = True
        if risk.get('risk_level') == 'high':
            messages.append('检测到高危风险表达：建议立即联系当地急救/危机干预热线，或尽快前往医院精神科/急诊，并联系可信任亲友陪伴。')
        diagnosis = report_parts.get('diagnosis', {}).get('hypotheses', [])
        sanitized = []
        for item in diagnosis:
            if '确诊' in item:
                passed = False
                sanitized.append(item.replace('确诊', '疑似'))
            else:
                sanitized.append(item)
        return {
            'passed': passed,
            'safety_message': '；'.join(messages),
            'sanitized_diagnosis': sanitized,
            'output_rules': ['禁止确诊', '高危风险优先', '建议线下专业评估', '保护隐私与数据脱敏'],
        }
