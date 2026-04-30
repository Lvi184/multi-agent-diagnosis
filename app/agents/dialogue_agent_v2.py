#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话引导 Agent V2 - 真正的心理咨询式引导

核心设计理念：
1. 分步引导，有温度的对话，不是机械问卷
2. 共情回应：理解、认可、安慰用户的感受
3. 深入询问：发现负性情绪后，追问具体原因和细节
4. 主动风险筛查：专门询问自杀/自伤想法
5. 自然的对话节奏，像真实的咨询师交流
"""
from typing import Dict, Any, List, Tuple
from app.core.session_manager import SessionState, SessionStatus
import re


class DialogueGuideAgentV2:
    """
    V2版本对话引导Agent - 心理咨询式引导
    
    引导流程：
    1. 开场问候 → 邀请描述感受
    2. 心情状态：最近心情怎么样？→ 深入询问原因
    3. 睡眠情况：睡得好吗？→ 入睡、早醒、多梦等
    4. 精力状态：有没有觉得很累、没劲？
    5. 负性事件：最近发生了什么特别的事情吗？
    6. 既往情况：之前有过类似情况吗？
    7. 用药情况：目前在吃药吗？
    8. 风险筛查：有没有过不想活的想法？（主动、温和地问）
    9. 量表评估：PHQ-9 / GAD-7
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
        
        # 对话阶段定义
        self.conversation_stages = [
            'init',              # 初始状态
            'mood_deep',         # 深入询问心情
            'sleep',             # 询问睡眠
            'energy',            # 询问精力
            'negative_event',    # 询问负性事件
            'medical_history',   # 既往史
            'medication',        # 用药史
            'risk_screen',       # 风险筛查
            'phq9_check',        # PHQ-9 是否已知分数
            'phq9_question',     # PHQ-9 做题
            'gad7_check',        # GAD-7 是否已知分数
            'gad7_question',     # GAD-7 做题
            'complete',          # 完成，进入诊断
        ]
        
        # 共情回应模板（根据不同场景选择）
        self.empathy_responses = {
            'bad_mood': [
                "我理解，这种感觉确实不好受。",
                "听起来你最近过得不太容易。",
                "我能感受到你的心情不太好。",
                "这种状态一定让你很疲惫吧。",
            ],
            'sleep_bad': [
                "睡不好真的很影响心情和精力。",
                "睡眠问题确实很让人困扰。",
                "能睡个好觉真的太重要了，我理解你的感受。",
            ],
            'tired': [
                "总是觉得累的话，做什么事情都会很吃力的。",
                "身心疲惫的感觉确实不好受。",
            ],
            'negative_event': [
                "发生这样的事情，一定让你很难过吧。",
                "听起来你经历了不少。",
                "这种情况换了谁都会觉得压力很大的。",
            ],
            'suicide_risk': [
                "有这样的想法并不奇怪，很多人在特别困难的时候都会有类似的念头。",
                "谢谢你愿意告诉我，这很重要。",
                "我理解你现在可能觉得很难熬，但请一定记得，情况是会变好的。",
            ],
        }
    
    def _get_empathy(self, category: str) -> str:
        """获取随机的共情回应"""
        import random
        responses = self.empathy_responses.get(category, ["我理解你的感受。"])
        return random.choice(responses)
    
    def _extract_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本中是否包含任一关键词"""
        text_lower = text.lower()
        return any(k in text_lower for k in keywords)
    
    def _add_symptom(self, session: SessionState, symptom: str):
        """添加症状（去重）"""
        if symptom not in session.symptoms:
            session.symptoms.append(symptom)
    
    def process_message(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """
        处理用户消息，返回更新的状态和下一个问题
        
        这是一个有温度的对话，不是机械问卷
        """
        session.add_input(user_message)
        
        # 获取当前阶段
        current_stage = getattr(session, 'conversation_stage', 'init')
        
        # 初始化：只有真正的第一轮对话才进入 init
        # （避免 conversation_stage 已更新，但 session.status 仍为 INIT 导致死循环）
        if current_stage == 'init':
            return self._handle_init(session, user_message)
        
        # 根据当前阶段分发处理
        stage_handlers = {
            'mood_deep': self._handle_mood_deep,
            'sleep': self._handle_sleep,
            'energy': self._handle_energy,
            'negative_event': self._handle_negative_event,
            'medical_history': self._handle_medical_history,
            'medication': self._handle_medication,
            'risk_screen': self._handle_risk_screen,
            'phq9_check': self._handle_phq9_check,
            'gad7_check': self._handle_gad7_check,
        }
        
        # 量表问题处理
        if current_stage.startswith('phq9_') and current_stage != 'phq9_check':
            return self._handle_phq9_question(session, user_message)
        if current_stage.startswith('gad7_') and current_stage != 'gad7_check':
            return self._handle_gad7_question(session, user_message)
        
        # 调用对应阶段的处理函数
        handler = stage_handlers.get(current_stage)
        if handler:
            return handler(session, user_message)
        
        # 默认：进入下一阶段
        return self._next_stage(session)
    
    def _handle_init(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理初始状态"""
        # 提取初始输入中的症状关键词
        has_mood_issue = self._extract_keywords(user_message, [
            '不好', '差', '低落', '抑郁', '难过', '伤心', '郁闷', '烦躁', '焦虑',
            '心情', '情绪', '没劲', '没兴趣', '不想动'
        ])
        has_sleep_issue = self._extract_keywords(user_message, [
            '睡不着', '失眠', '睡不好', '早醒', '多梦', '熬夜', '睡眠'
        ])
        
        # 记录初始症状
        if has_mood_issue:
            self._add_symptom(session, '情绪低落')
        if has_sleep_issue:
            self._add_symptom(session, '睡眠问题')
        
        # 设置对话阶段，同时更新 session.status，避免死循环
        session.conversation_stage = 'mood_deep'
        session.status = SessionStatus.COLLECTING_SYMPTOMS
        
        # 共情 + 深入询问
        if has_mood_issue:
            response = f"""{self._get_empathy('bad_mood')}

我想多了解一些：
你这种心情不好的状态持续多久了？是一直这样，还是时好时坏？"""
        else:
            response = f"""好的，谢谢你愿意和我分享。

首先想了解一下：
你最近的心情怎么样？是平静、开心，还是有些低落或者烦躁呢？"""
        
        return self._make_state_update(session, response)
    
    def _handle_mood_deep(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """深入询问心情状态"""
        # 提取持续时间
        session.duration = user_message
        
        # 检查是否有严重情绪问题的描述
        has_serious = self._extract_keywords(user_message, [
            '一直', '每天', '总是', '很严重', '特别', '非常', '想死', '不想活'
        ])
        if has_serious:
            self._add_symptom(session, '持续情绪低落')
        
        # 共情回应后，询问睡眠
        session.conversation_stage = 'sleep'
        
        response = f"""{self._get_empathy('bad_mood')}

那睡眠情况怎么样呢？
是入睡困难？容易早醒？还是睡得特别多但还是觉得累？"""
        
        return self._make_state_update(session, response)
    
    def _handle_sleep(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """询问睡眠情况"""
        session.sleep_info = user_message
        
        # 提取睡眠问题
        has_sleep_bad = self._extract_keywords(user_message, [
            '不好', '困难', '睡不着', '失眠', '早醒', '多梦', '差', '累'
        ])
        if has_sleep_bad:
            self._add_symptom(session, '睡眠障碍')
        
        # 共情回应后，询问精力
        session.conversation_stage = 'energy'
        
        response = f"""{self._get_empathy('sleep_bad')}

那精力方面呢？
有没有觉得总是很疲惫、没力气，或者以前喜欢的事情现在都不想做了？"""
        
        return self._make_state_update(session, response)
    
    def _handle_energy(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """询问精力状态"""
        session.energy_info = user_message
        
        # 提取精力问题
        has_energy_issue = self._extract_keywords(user_message, [
            '累', '疲惫', '没劲', '没力气', '不想动', '没兴趣', '不想做'
        ])
        if has_energy_issue:
            self._add_symptom(session, '精力减退')
        
        # 共情回应后，询问负性事件
        session.conversation_stage = 'negative_event'
        
        response = f"""{self._get_empathy('tired')}

我想了解一下，最近有发生什么特别的事情吗？
比如工作压力、感情问题、家庭变故，或者其他让你觉得有压力的事情？"""
        
        return self._make_state_update(session, response)
    
    def _handle_negative_event(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """询问负性事件"""
        session.negative_event = user_message
        
        # 检查是否提到了具体的压力源
        has_event = not self._extract_keywords(user_message, ['没有', '没什么', '还好', '不知道'])
        if has_event and len(user_message) > 5:
            self._add_symptom(session, '存在压力源')
        
        # 共情回应后，询问既往史
        session.conversation_stage = 'medical_history'
        
        if has_event and len(user_message) > 5:
            response = f"""{self._get_empathy('negative_event')}

谢谢你愿意和我说这些，把事情说出来本身就很不容易了。

我再问一下：你之前有过类似的情况吗？或者之前有没有被诊断过心理相关的问题？"""
        else:
            response = f"""好的。

那你之前有过类似的情况吗？或者之前有没有被诊断过心理相关的问题？"""
        
        return self._make_state_update(session, response)
    
    def _handle_medical_history(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """询问既往史"""
        session.medical_history = user_message
        
        # 询问用药史
        session.conversation_stage = 'medication'
        
        response = f"""了解了。

那你目前有没有在服用什么药物呢？比如抗抑郁药、安眠药，或者其他的药物？"""
        
        return self._make_state_update(session, response)
    
    def _handle_medication(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """询问用药史"""
        session.medication_history = user_message
        
        # ===== 重要：主动风险筛查 =====
        session.conversation_stage = 'risk_screen'
        
        response = f"""好的，谢谢你告诉我这些信息。

接下来有一个很重要的问题我想问问你，希望你不要介意：

你最近有没有过"不想活了"、"活着没意思"，或者伤害自己的想法？
哪怕只是一闪而过的念头，都可以告诉我。"""
        
        return self._make_state_update(session, response)
    
    def _handle_risk_screen(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """风险筛查 - 主动询问自杀/自伤风险"""
        session.risk_screen_result = user_message
        
        # 检查是否有自杀风险（先检查否定词，避免误匹配）
        # 先判断：用户明确说没有
        no_risk = self._extract_keywords(user_message, [
            '没有', '没有过', '没', '不会', '从不', '完全没有', '从来没有'
        ])
        # 再判断：用户明确表示有（避免"有"被"没有"误匹配）
        has_risk = self._extract_keywords(user_message, [
            '是的', '想过', '有过', '有时候会', '偶尔会', '有点',
            '不想活', '想死', '自杀', '自伤', '活着没意思', '死掉',
            '有一点', '有一些'
        ])
        
        # ===== 关键修复：如果有否定词，优先认为没有风险 =====
        # 避免"没有"中的"有"字被误匹配
        if no_risk:
            has_risk = False
        
        if has_risk:
            self._add_symptom(session, '存在自杀/自伤风险')
            # 有风险：共情 + 进一步确认 + 提醒
            session.has_suicide_risk = True
            response = f"""{self._get_empathy('suicide_risk')}

谢谢你愿意告诉我，这真的很重要。
如果你觉得这种想法很强烈，甚至控制不住，一定要立刻联系身边的人，或者去医院，好吗？

现在我们来做两个简单的量表评估，帮助更全面地了解你的情况。

首先是 PHQ-9 抑郁量表：
你之前做过这个量表吗？知道自己的分数吗？
• 如果知道，直接告诉我分数（0-27分）
• 如果不知道，我带你一步步完成（共9题，很快的）"""
        else:
            # 没有风险：温和回应，继续量表评估
            session.has_suicide_risk = False
            response = f"""好的，我了解了。

现在我们来做两个简单的量表评估，帮助更全面地了解你的情况。

首先是 PHQ-9 抑郁量表：
你之前做过这个量表吗？知道自己的分数吗？
• 如果知道，直接告诉我分数（0-27分）
• 如果不知道，我带你一步步完成（共9题，很快的）"""
        
        # 进入量表检查阶段
        session.conversation_stage = 'phq9_check'
        session.status = SessionStatus.COLLECTING_SCALE
        
        return self._make_state_update(session, response)
    
    def _handle_phq9_check(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理 PHQ-9 是否已知分数"""
        numbers = re.findall(r'\d+', user_message)
        know_score = self._extract_keywords(user_message, ['知道', '做过', '记得', '是', '对', '有'])
        no_score = self._extract_keywords(user_message, ['不知道', '没做过', '不记得', '没有', '不清楚'])
        
        if numbers:
            # 用户直接说了分数
            score = int(numbers[0])
            if 'PHQ9' not in session.scales:
                session.scales['PHQ9'] = {'items': {}, 'score': 0}
            session.scales['PHQ9']['score'] = max(0, min(score, 27))
            
            # 跳到 GAD-7 检查
            session.conversation_stage = 'gad7_check'
            phq9_score = session.scales['PHQ9']['score']
            response = f"""好的，已记录 PHQ-9 分数：{phq9_score} 分

接下来是 GAD-7 焦虑量表：
你之前做过这个量表吗？知道自己的分数吗？
• 如果知道，直接告诉我分数（0-21分）
• 如果不知道，我带你一步步完成（共7题）"""
            
        elif know_score and not numbers:
            # 用户表示知道但没说具体分数
            response = "好的，请告诉我你的 PHQ-9 分数是多少（0-27分）？"
            
        elif no_score:
            # 用户表示不知道，开始引导做题
            session.conversation_stage = 'phq9_0'
            response = f"""好的，我们来一起完成 PHQ-9 抑郁量表（共9题）：

{self.phq9_questions[0]}
{self.score_options}"""
            
        else:
            # 默认：引导做题
            session.conversation_stage = 'phq9_0'
            response = f"""好的，我们来一起完成：

{self.phq9_questions[0]}
{self.score_options}"""
        
        return self._make_state_update(session, response)
    
    def _handle_phq9_question(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理 PHQ-9 题目回答"""
        # 解析评分
        score = self._parse_score(user_message)
        
        # 提取当前题号
        current_q = session.conversation_stage
        q_idx = int(current_q.split('_')[1]) if '_' in current_q else 0
        
        # 保存当前问题分数
        if 'PHQ9' not in session.scales:
            session.scales['PHQ9'] = {'items': {}, 'score': 0}
        session.scales['PHQ9']['items'][f'q{q_idx+1}'] = score
        
        # 更新总分
        session.scales['PHQ9']['score'] = sum(session.scales['PHQ9']['items'].values())
        
        # 下一个问题
        if q_idx + 1 < len(self.phq9_questions):
            session.conversation_stage = f'phq9_{q_idx+1}'
            response = f"""第 {q_idx+1} 题已记录（得分：{score}）

PHQ-9 第 {q_idx+2} 题：
{self.phq9_questions[q_idx+1]}
{self.score_options}"""
        else:
            # PHQ-9 完成，进入 GAD-7 检查
            session.conversation_stage = 'gad7_check'
            phq9_total = session.scales['PHQ9']['score']
            response = f"""✅ PHQ-9 完成！总得分：{phq9_total} 分

接下来是 GAD-7 焦虑量表：
你之前做过这个量表吗？知道自己的分数吗？
• 如果知道，直接告诉我分数（0-21分）
• 如果不知道，我带你一步步完成（共7题）"""
        
        return self._make_state_update(session, response)
    
    def _handle_gad7_check(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理 GAD-7 是否已知分数"""
        numbers = re.findall(r'\d+', user_message)
        know_score = self._extract_keywords(user_message, ['知道', '做过', '记得', '是', '对', '有'])
        no_score = self._extract_keywords(user_message, ['不知道', '没做过', '不记得', '没有', '不清楚'])
        
        if numbers:
            # 用户直接说了分数
            score = int(numbers[0])
            if 'GAD7' not in session.scales:
                session.scales['GAD7'] = {'items': {}, 'score': 0}
            session.scales['GAD7']['score'] = max(0, min(score, 21))
            
            # 量表全部完成，进入诊断
            gad7_score = session.scales['GAD7']['score']
            phq9_score = session.scales.get('PHQ9', {}).get('score', 0)
            session.status = SessionStatus.DIAGNOSING
            session.conversation_stage = 'complete'
            
            response = f"""好的，已记录 GAD-7 分数：{gad7_score} 分

📊 正在为您生成心理健康评估报告...

  PHQ-9（抑郁）：{phq9_score} 分
  GAD-7（焦虑）：{gad7_score} 分

🔄 正在通过多Agent系统进行综合分析，请稍候...
（大约需要5-10秒）"""
            
        elif know_score and not numbers:
            # 用户表示知道但没说具体分数
            response = "好的，请告诉我你的 GAD-7 分数是多少（0-21分）？"
            
        elif no_score:
            # 用户表示不知道，开始引导做题
            session.conversation_stage = 'gad7_0'
            response = f"""好的，我们来一起完成 GAD-7 焦虑量表（共7题）：

{self.gad7_questions[0]}
{self.score_options}"""
            
        else:
            # 默认：引导做题
            session.conversation_stage = 'gad7_0'
            response = f"""好的，我们来一起完成：

{self.gad7_questions[0]}
{self.score_options}"""
        
        return self._make_state_update(session, response)
    
    def _handle_gad7_question(self, session: SessionState, user_message: str) -> Tuple[Dict[str, Any], str]:
        """处理 GAD-7 题目回答"""
        # 解析评分
        score = self._parse_score(user_message)
        
        # 提取当前题号
        current_q = session.conversation_stage
        q_idx = int(current_q.split('_')[1]) if '_' in current_q else 0
        
        # 保存当前问题分数
        if 'GAD7' not in session.scales:
            session.scales['GAD7'] = {'items': {}, 'score': 0}
        session.scales['GAD7']['items'][f'q{q_idx+1}'] = score
        
        # 更新总分
        session.scales['GAD7']['score'] = sum(session.scales['GAD7']['items'].values())
        
        # 下一个问题
        if q_idx + 1 < len(self.gad7_questions):
            session.conversation_stage = f'gad7_{q_idx+1}'
            response = f"""第 {q_idx+1} 题已记录（得分：{score}）

GAD-7 第 {q_idx+2} 题：
{self.gad7_questions[q_idx+1]}
{self.score_options}"""
        else:
            # GAD-7 完成，进入诊断
            gad7_total = session.scales['GAD7']['score']
            phq9_total = session.scales.get('PHQ9', {}).get('score', 0)
            session.status = SessionStatus.DIAGNOSING
            session.conversation_stage = 'complete'
            
            response = f"""✅ GAD-7 完成！总得分：{gad7_total} 分

📊 信息收集已全部完成！

  PHQ-9（抑郁）：{phq9_total} 分
  GAD-7（焦虑）：{gad7_total} 分

现在我将为您进行综合分析和评估，请稍候..."""
        
        return self._make_state_update(session, response)
    
    def _parse_score(self, text: str) -> int:
        """解析用户输入的评分"""
        numbers = re.findall(r'\d+', text)
        if numbers:
            score = int(numbers[0])
            if 0 <= score <= 3:
                return score
        
        # 文本匹配
        text_lower = text.lower()
        if self._extract_keywords(text, ['完全', '没有', '从不', '0']):
            return 0
        elif self._extract_keywords(text, ['几天', '好几天', '偶尔', '1']):
            return 1
        elif self._extract_keywords(text, ['一半', '多数', '经常', '2']):
            return 2
        elif self._extract_keywords(text, ['每天', '几乎', '总是', '3']):
            return 3
        
        return 0
    
    def _make_state_update(self, session: SessionState, response: str) -> Tuple[Dict[str, Any], str]:
        """构造状态更新返回值"""
        collected = {
            'symptoms': session.symptoms,
            'duration': getattr(session, 'duration', None),
            'medical_history': getattr(session, 'medical_history', None),
            'medication_history': getattr(session, 'medication_history', None),
            'has_suicide_risk': getattr(session, 'has_suicide_risk', None),
        }
        
        return {
            'status': session.status.value,  # 返回字符串，不是 Enum
            'mode': 'guided',
            'collected_so_far': collected,
            'collected_info': collected,  # 两个都返回，兼容前端
        }, response


# 全局单例
_dialogue_agent_v2 = None


def get_dialogue_agent_v2() -> DialogueGuideAgentV2:
    """获取 V2 对话引导 Agent 单例"""
    global _dialogue_agent_v2
    if _dialogue_agent_v2 is None:
        _dialogue_agent_v2 = DialogueGuideAgentV2()
    return _dialogue_agent_v2
