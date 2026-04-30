#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意图分类器 - 前置判断用户意图，避免非诊断场景强制走完整流程
"""
from typing import Dict, Any, Tuple, Optional
import re


class IntentType:
    """意图类型枚举"""
    GREETING = 'greeting'           # 问候/打招呼
    CHITCHAT = 'chitchat'           # 闲聊/无关对话
    QUESTION_SYSTEM = 'question_system'  # 询问系统相关问题
    QUESTION_MEDICAL = 'question_medical'  # 询问医学相关问题
    SYMPTOM_REPORT = 'symptom_report'     # 症状报告/寻求诊断
    THANKS = 'thanks'               # 感谢
    GOODBYE = 'goodbye'             # 道别
    UNKNOWN = 'unknown'              # 未知


class IntentClassifier:
    """
    轻量级意图分类器 - 规则匹配为主，无需LLM调用
    
    功能：
    1. 快速识别用户意图，避免非诊断场景走完整流程
    2. 对简单问候、闲聊等直接回复，不进入诊断流程
    3. 只有真正的症状报告才进入多Agent诊断流程
    """
    
    def __init__(self):
        # 问候关键词
        self.greeting_patterns = [
            r'^[你您]好', r'^hi', r'^hello', r'^嗨', r'^在吗',
            r'^哈喽', r'^早上好', r'^下午好', r'^晚上好', r'^你在吗',
            r'^有人吗', r'^在不',
        ]
        
        # 感谢关键词
        self.thanks_patterns = [
            r'谢谢', r'感谢', r'多谢', r'谢谢了', r'谢了',
        ]
        
        # 道别关键词
        self.goodbye_patterns = [
            r'再见', r'拜拜', r'再会', r'下次见', r'拜拜了',
        ]
        
        # 系统问题关键词
        self.system_patterns = [
            r'你是谁', r'你叫什么', r'你能做什么', r'怎么用', r'怎么使用',
            r'使用说明', r'功能', r'帮助', r'怎么操作', r'介绍一下',
            r'你是什么', r'这是什么', r'你是ai吗', r'你是机器人吗',
        ]
        
        # 症状关键词（触发诊断流程）
        self.symptom_patterns = [
            r'情绪', r'抑郁', r'焦虑', r'失眠', r'睡不着', r'睡眠',
            r'心情', r'难过', r'难受', r'痛苦', r'压力', r'紧张',
            r'不想活', r'自杀', r'想死', r'没意思', r'活着',
            r'没兴趣', r'提不起劲', r'乏力', r'疲劳', r'累',
            r'担心', r'害怕', r'恐慌', r'烦躁', r'易怒',
            r'胃口', r'食欲', r'吃不下', r'吃太多',
            r'症状', r'不舒服', r'难受', r'得病', r'生病',
            r'持续', r'多久', r'最近', r'这几天', r'这几周', r'这几个月',
            r'评估', r'诊断', r'检查', r'筛查',
        ]
        
        # 量表关键词
        self.scale_patterns = [
            r'phq', r'gad', r'hamd', r'hama', r'量表', r'评分',
            r'得分', r'分数',
        ]
        
        # 医学问题关键词
        self.medical_patterns = [
            r'什么是', r'怎么办', r'如何', r'怎么治疗', r'怎么缓解',
            r'应该', r'严重吗', r'正常吗', r'有什么药', r'吃什么药',
            r'医生', r'医院', r'就诊', r'看病',
        ]
        
        # 回复模板
        self.response_templates = {
            IntentType.GREETING: [
                "你好！我是心理健康辅助筛查助手。如果您有情绪、睡眠等方面的困扰需要评估，都可以告诉我。",
                "您好！请描述您的症状、持续时间等信息，我可以帮您进行初步筛查评估。",
            ],
            IntentType.THANKS: [
                "不客气！如果后续还有需要，随时可以再找我。",
                "不用谢！希望能对您有所帮助。",
            ],
            IntentType.GOODBYE: [
                "再见！祝您生活愉快，身体健康！",
                "拜拜！有需要随时可以再来找我。",
            ],
            IntentType.QUESTION_SYSTEM: [
                "我是多Agent心理健康辅助筛查原型。我可以帮您进行心理健康初步筛查评估，请描述您的症状、持续时间、睡眠情况等，我会通过多Agent系统为您进行综合分析。",
                "这是一个心理健康辅助筛查系统，使用10个专业Agent协同工作。请告诉我您的症状和相关信息，我就可以为您进行评估。",
            ],
            IntentType.QUESTION_MEDICAL: [
                "这是一个很好的问题！不过我只能提供初步筛查建议，不能替代专业诊断。如果您有具体的症状，可以告诉我，我帮您进行初步评估。建议您有任何疑问都咨询专业的精神科/心理科医生。",
                "关于医学问题，我的建议仅供参考。如果您有具体症状请描述一下，我可以帮您做初步筛查。最终诊断和建议还是建议您咨询专业医生。",
            ],
            IntentType.CHITCHAT: [
                "我们聊聊心理健康相关的话题吧！如果您有什么情绪或睡眠方面的困扰需要评估，请告诉我。",
                "我是心理健康评估助手，请告诉我您的症状或相关情况，我来帮您做初步筛查。",
            ],
        }
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        分类用户意图
        
        Returns:
            (意图类型, 置信度 0-1)
        """
        text_clean = text.strip().lower()
        
        # 1. 先检查是否包含症状关键词（最高优先级）
        symptom_count = sum(1 for p in self.symptom_patterns if re.search(p, text_clean, re.IGNORECASE))
        scale_count = sum(1 for p in self.scale_patterns if re.search(p, text_clean, re.IGNORECASE))
        
        if symptom_count >= 2 or scale_count >= 1:
            return IntentType.SYMPTOM_REPORT, 0.9
        
        # 2. 检查问候（纯问候，没有症状关键词）
        for pattern in self.greeting_patterns:
            if re.match(pattern, text_clean, re.IGNORECASE):
                # 检查是否同时包含症状词
                if symptom_count == 0 and len(text) <= 10:
                    return IntentType.GREETING, 0.85
                break
        
        # 3. 检查感谢
        for pattern in self.thanks_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return IntentType.THANKS, 0.8
        
        # 4. 检查道别
        for pattern in self.goodbye_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return IntentType.GOODBYE, 0.8
        
        # 5. 检查系统问题
        for pattern in self.system_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return IntentType.QUESTION_SYSTEM, 0.8
        
        # 6. 检查医学问题
        medical_count = sum(1 for p in self.medical_patterns if re.search(p, text_clean, re.IGNORECASE))
        if medical_count >= 1 and symptom_count <= 1:
            return IntentType.QUESTION_MEDICAL, 0.7
        
        # 7. 如果有至少一个症状词，进入诊断（单症状词也可能是用户在报告）
        if symptom_count >= 1:
            return IntentType.SYMPTOM_REPORT, 0.7
        
        # 9. 太短的文本，闲聊
        if len(text) <= 5:
            return IntentType.CHITCHAT, 0.5
        
        return IntentType.UNKNOWN, 0.3
    
    def get_response(self, intent: str) -> str:
        """根据意图获取默认回复"""
        import random
        responses = self.response_templates.get(intent, [])
        if responses:
            return random.choice(responses)
        return "请描述您的症状、持续时间等信息，我来帮您进行初步筛查评估。"
    
    def should_enter_diagnosis(self, intent: str) -> bool:
        """判断是否应该进入完整诊断流程"""
        return intent in [IntentType.SYMPTOM_REPORT]


# 全局单例
_intent_classifier = None


def get_intent_classifier() -> IntentClassifier:
    """获取意图分类器单例"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
