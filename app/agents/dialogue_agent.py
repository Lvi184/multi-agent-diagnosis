#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话引导 Agent - 负责多轮对话，逐步收集患者信息
"""
from typing import Dict, Any, List, Tuple
from app.core.session_manager import SessionState, SessionStatus


class DialogueGuideAgent:
    """
    对话引导 Agent - 智能引导患者完成信息采集
    
    功能：
    1. 识别当前收集进度
    2. 生成下一个问题
    3. 解析用户回答，提取信息
    4. 判断何时进入诊断阶段
    """
    
    def __init__(self):
        # PHQ-9 抑郁症筛查量表问题
        self.phq9_questions = [
            "1. 做事提不起劲或没有兴趣？",
            "2. 感到心情低落、沮丧或绝望？",
            "3. 入睡困难、睡不安稳或睡眠过多？",
            "4. 感到疲倦或没有活力？",
            "5. 食欲不振或吃太多？",
            "6. 觉得自己很糟，或觉得自己很失败，或让自己或家人失望？",
            "7. 对事物专注有困难，例如阅读报纸或看电视时？",
            "8. 动作或说话速度缓慢到别人已经觉察？或相反，变得比平时更加烦躁或坐立不安？",
            "9. 有不如死掉或用某种方式伤害自己的念头？",
        ]
        
        # GAD-7 焦虑症筛查量表问题
        self.gad7_questions = [
            "1. 感到紧张、焦虑或急切？",
            "2. 无法停止或控制担忧？",
            "3. 对各种各样的事情担忧过多？",
            "4. 很难放松下来？",
            "5. 如此焦躁以至于难以静坐？",
            "6. 变得容易烦恼或急躁？",
            "7. 感到似乎将有可怕的事情发生而害怕？",
        ]
        
        # 评分选项
        self.score_options = "请选择：0=完全不会，1=好几天，2=一半以上天数，3=几乎每天"
        
        # 采集阶段定义
        self.phases = [
            'symptoms',      # 症状采集
            'duration',      # 持续时间
            'history',       # 既往史
            'medication',    # 用药史
            'phq9',         # PHQ-9 量表
            'gad7',         # GAD-7 量表
            'summary',      # 总结确认
        ]
    
    def process_message(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """
        处理用户消息，返回更新的状态和下一个问题
        
        Args:
            session: 会话状态
            user_message: 用户输入消息
            
        Returns:
            (更新的状态字典, 下一个问题/回复)
        """
        session.add_input(user_message)
        
        # 初始问候
        if session.status == SessionStatus.INIT:
            return self._handle_init(session, user_message)
        
        # 正在采集症状
        elif session.status == SessionStatus.COLLECTING_SYMPTOMS:
            return self._handle_collecting_symptoms(session, user_message)
        
        # 正在采集量表
        elif session.status == SessionStatus.COLLECTING_SCALE:
            return self._handle_collecting_scale(session, user_message)
        
        # 其他状态
        return self._default_response(session)
    
    def _handle_init(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理初始状态"""
        # 提取初始输入中的症状
        symptoms = self._extract_symptoms(user_message)
        for symptom in symptoms:
            session.add_symptom(symptom)
        
        # 检查是否已经有量表分数
        scales = self._extract_scale_scores(user_message)
        if scales:
            session.scales.update(scales)
        
        # 决定下一步
        if session.scales.get('PHQ9') or session.scales.get('GAD7'):
            # 已有量表分数，直接进入诊断
            session.status = SessionStatus.DIAGNOSING
            response = f"好的，我已经了解您的情况。\n\n您提到的症状：{', '.join(session.symptoms) if session.symptoms else '暂无'}\n\n现在我将为您进行综合评估，请稍候..."
            return {'status': SessionStatus.DIAGNOSING, 'symptoms': session.symptoms, 'mode': 'quick'}, response
        elif len(symptoms) == 0:
            # 没有检测到明显症状，引导用户进一步描述
            session.status = SessionStatus.COLLECTING_SYMPTOMS
            session.questions_asked = 0
            
            response = """您好！我是心理健康辅助筛查助手。

为了更好地帮助您，请简单描述一下您的情况，比如：
• 最近的心情怎么样？
• 睡眠情况如何？
• 有没有什么特别的困扰？
• 或者您想评估哪方面的问题？"""
            
            return {'status': SessionStatus.COLLECTING_SYMPTOMS, 'symptoms': [], 'mode': 'guided'}, response
        else:
            # 检测到症状，开始引导评估
            session.status = SessionStatus.COLLECTING_SYMPTOMS
            session.questions_asked = 0
            
            response = f"""好的，我了解到您提到了：{', '.join(symptoms)}

接下来我会问您几个问题，帮助我更全面地了解您的情况。

首先，请问：
您这些症状持续多久了？（例如：几天、几周、几个月）"""
            
            return {'status': SessionStatus.COLLECTING_SYMPTOMS, 'symptoms': symptoms, 'mode': 'guided'}, response
    
    def _handle_collecting_symptoms(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理症状采集中"""
        session.questions_asked += 1
        
        # 提取回答中的信息
        if session.questions_asked == 1:
            # 第一个问题是持续时间
            session.duration = user_message
            
            response = f"""好的，持续时间：{user_message}

接下来请问：
您之前是否有过类似的情况？是否有其他精神疾病病史？"""
            
        elif session.questions_asked == 2:
            # 第二个问题是既往史
            session.medical_history = user_message
            
            response = f"""了解了。

请问您目前是否在服用任何药物？"""
            
        elif session.questions_asked == 3:
            # 第三个问题是用药史
            session.medication_history = user_message
            
            # 切换到量表采集阶段，先询问是否已知分数
            session.status = SessionStatus.COLLECTING_SCALE
            session.current_question = 'phq9_check'  # 特殊状态：检查是否知道分数
            
            response = f"""好的，谢谢您提供的信息。

接下来我们需要评估一下您的抑郁和焦虑情况。

首先问一下：
您之前做过 PHQ-9 抑郁量表吗？知道自己的分数吗？

• 如果知道，请直接告诉我分数（0-27分）
• 如果不知道，我带您一步步完成这个量表（共9题，很快的）"""
            
        else:
            # 已经问完基础问题，应该在量表阶段了
            session.status = SessionStatus.COLLECTING_SCALE
            session.current_question = 'phq9_0'
            
            response = f"""现在我们来做量表评估。

PHQ-9 抑郁症筛查量表 第1题：
{self.phq9_questions[0]}
{self.score_options}"""
        
        return {'status': session.status}, response
    
    def _handle_collecting_scale(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理量表采集中"""
        current_q = session.current_question
        
        # ===== PHQ-9：检查是否已知分数
        if current_q == 'phq9_check':
            # 检查用户是否表示知道分数（包含数字或者表示"知道""做过"
            import re
            numbers = re.findall(r'\d+', user_message)
            know_score = any(keyword in user_message for keyword in ['知道', '做过', '记得', '是', '对', '有', '知道', '了解'])
            
            if numbers:
                # 用户直接说了分数
                score = int(numbers[0])
                if 'PHQ9' not in session.scales:
                    session.scales['PHQ9'] = {'items': {}, 'score': 0}
                session.scales['PHQ9']['score'] = max(0, min(score, 27))
                
                # 跳到 GAD-7 检查
                session.current_question = 'gad7_check'
                phq9_score = session.scales['PHQ9']['score']
                response = f"""好的，已记录您的 PHQ-9 分数：{phq9_score} 分

接下来问一下：
您之前做过 GAD-7 焦虑量表吗？知道自己的分数吗？

• 如果知道，请直接告诉我分数（0-21分）
• 如果不知道，我带您一步步完成这个量表（共7题）"""
                
            elif know_score:
                # 用户表示知道但没说具体分数，让用户输入
                response = "好的，请告诉我您的 PHQ-9 分数是多少（0-27分）？"
                
            else:
                # 用户表示不知道，开始引导做题
                session.current_question = 'phq9_0'
                response = f"""好的，我们来一起完成 PHQ-9 抑郁量表（共9题）：

{self.phq9_questions[0]}
{self.score_options}"""
            
            return {'status': SessionStatus.COLLECTING_SCALE, 'scales': session.scales}, response
        
        # ===== GAD-7：检查是否已知分数
        if current_q == 'gad7_check':
            import re
            numbers = re.findall(r'\d+', user_message)
            know_score = any(keyword in user_message for keyword in ['知道', '做过', '记得', '是', '对', '有', '知道', '了解'])
            
            if numbers:
                # 用户直接说了分数
                score = int(numbers[0])
                if 'GAD7' not in session.scales:
                    session.scales['GAD7'] = {'items': {}, 'score': 0}
                session.scales['GAD7']['score'] = max(0, min(score, 21))
                
                # 量表完成，进入诊断
                gad7_score = session.scales['GAD7']['score']
                phq9_score = session.scales.get('PHQ9', {}).get('score', 0)
                session.status = SessionStatus.DIAGNOSING
                
                response = f"""好的，已记录您的 GAD-7 分数：{gad7_score} 分

📊 量表评估已全部完成！

  PHQ-9（抑郁）：{phq9_score} 分
  GAD-7（焦虑）：{gad7_score} 分

现在我将为您进行综合分析和评估，请稍候..."""
                
            elif know_score:
                # 用户表示知道但没说具体分数，让用户输入
                response = "好的，请告诉我您的 GAD-7 分数是多少（0-21分）？"
                
            else:
                # 用户表示不知道，开始引导做题
                session.current_question = 'gad7_0'
                response = f"""好的，我们来一起完成 GAD-7 焦虑量表（共7题）：

{self.gad7_questions[0]}
{self.score_options}"""
            
            return {'status': session.status, 'scales': session.scales}, response
        
        # 解析评分（正常做题流程）
        score = self._parse_score(user_message)
        
        if current_q.startswith('phq9_'):
            # PHQ-9 量表
            q_idx = int(current_q.split('_')[1])
            
            # 保存当前问题分数
            if 'PHQ9' not in session.scales:
                session.scales['PHQ9'] = {'items': {}, 'score': 0}
            session.scales['PHQ9']['items'][f'q{q_idx+1}'] = score
            
            # 更新总分
            session.scales['PHQ9']['score'] = sum(session.scales['PHQ9']['items'].values())
            
            # 下一个问题
            if q_idx + 1 < len(self.phq9_questions):
                session.current_question = f'phq9_{q_idx+1}'
                response = f"""第 {q_idx+1} 题已记录（得分：{score}）

PHQ-9 第 {q_idx+2} 题：
{self.phq9_questions[q_idx+1]}
{self.score_options}"""
            else:
                # PHQ-9 完成，询问 GAD-7 是否知道分数
                session.current_question = 'gad7_check'
                phq9_total = sum(session.scales['PHQ9']['items'].values())
                session.scales['PHQ9']['score'] = phq9_total
                response = f"""✅ PHQ-9 完成！总得分：{phq9_total} 分

接下来问一下：
您之前做过 GAD-7 焦虑量表吗？知道自己的分数吗？

• 如果知道，请直接告诉我分数（0-21分）
• 如果不知道，我带您一步步完成这个量表（共7题）"""
        
        elif current_q.startswith('gad7_'):
            # GAD-7 量表
            q_idx = int(current_q.split('_')[1])
            
            # 保存当前问题分数
            if 'GAD7' not in session.scales:
                session.scales['GAD7'] = {'items': {}, 'score': 0}
            session.scales['GAD7']['items'][f'q{q_idx+1}'] = score
            
            # 更新总分
            session.scales['GAD7']['score'] = sum(session.scales['GAD7']['items'].values())
            
            # 下一个问题
            if q_idx + 1 < len(self.gad7_questions):
                session.current_question = f'gad7_{q_idx+1}'
                response = f"""第 {q_idx+1} 题已记录（得分：{score}）

GAD-7 第 {q_idx+2} 题：
{self.gad7_questions[q_idx+1]}
{self.score_options}"""
            else:
                # GAD-7 完成，进入诊断阶段
                gad7_total = sum(session.scales['GAD7']['items'].values())
                session.scales['GAD7']['score'] = gad7_total
                phq9_total = session.scales.get('PHQ9', {}).get('score', 0)
                session.status = SessionStatus.DIAGNOSING
                
                response = f"""✅ GAD-7 完成！总得分：{gad7_total}

量表评估已全部完成！

📊 评估结果汇总：
- PHQ-9（抑郁）：{phq9_total} 分
- GAD-7（焦虑）：{gad7_total} 分

现在我将为您进行综合分析和评估，请稍候..."""
        
        else:
            # 默认开始 PHQ-9
            session.current_question = 'phq9_0'
            response = f"""我们开始量表评估。

PHQ-9 第1题：
{self.phq9_questions[0]}
{self.score_options}"""
        
        return {'status': session.status, 'scales': session.scales}, response
    
    def _parse_score(self, text: str) -> int:
        """解析用户输入的评分"""
        # 提取数字
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            score = int(numbers[0])
            if 0 <= score <= 3:
                return score
        
        # 文本匹配
        text = text.lower()
        if '完全' in text or '没有' in text or '0' in text:
            return 0
        elif '几天' in text or '1' in text:
            return 1
        elif '一半' in text or '多数' in text or '2' in text:
            return 2
        elif '每天' in text or '几乎' in text or '3' in text:
            return 3
        
        return 0  # 默认
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """从文本中提取症状关键词"""
        symptom_keywords = [
            '情绪低落', '心情差', '郁闷', '抑郁', '不高兴',
            '失眠', '睡不着', '睡眠', '早醒', '嗜睡',
            '兴趣减退', '没兴趣', '不想动', '没动力',
            '焦虑', '紧张', '担心', '害怕', '恐慌',
            '疲劳', '累', '没精力', '乏力',
            '自责', '内疚', '没用', '失败',
            '注意力', '不集中', '健忘',
            '自杀', '想死', '活着没意思', '自伤',
            '食欲', '吃太多', '没胃口',
            '坐立不安', '烦躁', '易怒',
            '幻觉', '妄想', '幻听',
        ]
        
        found = []
        for keyword in symptom_keywords:
            if keyword in text:
                found.append(keyword)
        
        return found if found else []
    
    def _extract_scale_scores(self, text: str) -> Dict[str, int]:
        """从文本中提取量表分数"""
        import re
        scales = {}
        
        # 匹配 PHQ9: 数字 或 PHQ-9: 数字
        phq9_match = re.search(r'(PHQ-?9|phq9)[:：\s]*(\d+)', text, re.IGNORECASE)
        if phq9_match:
            scales['PHQ9'] = int(phq9_match.group(2))
        
        # 匹配 GAD7: 数字
        gad7_match = re.search(r'(GAD-?7|gad7)[:：\s]*(\d+)', text, re.IGNORECASE)
        if gad7_match:
            scales['GAD7'] = int(gad7_match.group(2))
        
        return scales
    
    def _default_response(self, session: SessionState) -> Tuple[Dict[str, Any], str]:
        """默认回复"""
        response = "好的，我已经了解您的情况。现在开始进行综合评估..."
        session.status = SessionStatus.DIAGNOSING
        return {'status': SessionStatus.DIAGNOSING}, response


# 全局单例
_dialogue_agent = None


def get_dialogue_agent() -> DialogueGuideAgent:
    """获取对话引导 Agent 单例"""
    global _dialogue_agent
    if _dialogue_agent is None:
        _dialogue_agent = DialogueGuideAgent()
    return _dialogue_agent
