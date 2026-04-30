#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断编排器 V2 - 支持多轮对话模式（心理咨询式引导）
"""
from typing import Dict, Any, Tuple
from app.core.session_manager import (
    get_session_manager, SessionState, SessionStatus
)
from app.agents.dialogue_agent_v2 import get_dialogue_agent_v2
from app.graph.workflow import LangGraphDiagnosisWorkflow


class DiagnosisOrchestratorV2:
    """
    V2 版本编排器 - 支持两种模式
    
    模式一：快速诊断模式（已有量表分数）
      - 用户直接输入症状 + 量表分数
      - 单轮完成完整诊断
    
    模式二：引导评估模式（无量表分数）
      - 多轮对话逐步收集信息
      - 引导完成 PHQ-9 / GAD-7 量表
      - 收集完成后执行完整诊断
    """
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.dialogue_agent = get_dialogue_agent_v2()  # 使用 V2 心理咨询式引导
        self.diagnosis_workflow = LangGraphDiagnosisWorkflow()
    
    def _get_phq9_level(self, score: int) -> str:
        """PHQ-9 分数等级解释"""
        if score <= 4:
            return "正常/轻微"
        elif score <= 9:
            return "轻度"
        elif score <= 14:
            return "中度"
        elif score <= 19:
            return "中重度"
        else:
            return "重度"
    
    def _get_gad7_level(self, score: int) -> str:
        """GAD-7 分数等级解释"""
        if score <= 4:
            return "正常/轻微"
        elif score <= 9:
            return "轻度"
        elif score <= 14:
            return "中度"
        else:
            return "重度"
    
    def process_message(self, session_id: str, user_message: str, 
                       scale_answers: Dict = None, age: str = None, 
                       gender: str = None) -> Tuple[Dict[str, Any], str]:
        """
        处理用户消息，支持多轮对话
        
        Args:
            session_id: 会话ID
            user_message: 用户输入消息
            scale_answers: 预填写的量表答案（可选）
            age: 年龄（可选）
            gender: 性别（可选）
            
        Returns:
            (结果字典, 回复消息)
        """
        # 获取或创建会话
        session = self.session_manager.get_or_create(session_id)
        
        # ===== 优化：空消息轮询 =====
        if not user_message.strip():
            # 已有诊断结果，直接返回
            if session.status == SessionStatus.COMPLETED and session.diagnosis_result:
                # ===== 修复：确保返回 collected_info =====
                result_with_collected = dict(session.diagnosis_result)
                result_with_collected['collected_info'] = {
                    'symptoms': session.symptoms,
                    'duration': session.duration,
                    'medical_history': session.medical_history,
                    'medication_history': session.medication_history,
                    'scales': session.scales,
                }
                return result_with_collected, self._generate_final_report(session, session.diagnosis_result)
            # 处于诊断状态，运行诊断
            if session.status == SessionStatus.DIAGNOSING:
                diagnosis_result = self._run_diagnosis(session)
                final_response = self._generate_final_report(session, diagnosis_result)
                # ===== 修复：确保返回 collected_info =====
                result_with_collected = dict(diagnosis_result)
                result_with_collected['collected_info'] = {
                    'symptoms': session.symptoms,
                    'duration': session.duration,
                    'medical_history': session.medical_history,
                    'medication_history': session.medication_history,
                    'scales': session.scales,
                }
                return result_with_collected, final_response
        
        # 初始化会话元数据
        if age:
            session.age = age
        if gender:
            session.gender = gender
        if scale_answers:
            session.scales.update(scale_answers)
        
        # 检查：如果用户已经填写了量表分数（前端手动填写），直接进入快速诊断
        if session.status == SessionStatus.INIT:
            phq9_score = session.scales.get('PHQ9', 0)
            gad7_score = session.scales.get('GAD7', 0)
            if isinstance(phq9_score, (int, float)) and phq9_score > 0:
                session.status = SessionStatus.DIAGNOSING
                diagnosis_result = self._run_diagnosis(session)
                final_response = self._generate_final_report(session, diagnosis_result)
                return diagnosis_result, final_response
            if isinstance(gad7_score, (int, float)) and gad7_score > 0:
                session.status = SessionStatus.DIAGNOSING
                diagnosis_result = self._run_diagnosis(session)
                final_response = self._generate_final_report(session, diagnosis_result)
                return diagnosis_result, final_response
        
        # 如果是第一轮，先交给对话引导 Agent
        if (session.status == SessionStatus.INIT or 
            session.status == SessionStatus.COLLECTING_SYMPTOMS or
            session.status == SessionStatus.COLLECTING_SCALE):
            
            state_update, response = self.dialogue_agent.process_message(
                session, user_message
            )
            
            # 更新会话状态（排除 status 字段，避免覆盖 Enum 类型）
            for key, value in state_update.items():
                if key != 'status':  # status 由 session 自己管理，不要覆盖
                    setattr(session, key, value)
            
            # 如果收集完成，先返回"正在诊断"的提示，不要阻塞
            # 真正的诊断在下次轮询（空消息）时执行，让用户先看到等待提示
            if session.status == SessionStatus.DIAGNOSING:
                # ===== 关键优化：不立刻运行诊断，先返回提示 =====
                # 这样用户能立刻看到"正在分析"的反馈，不会觉得卡住
                # 注意：session.status 保持 Enum 类型，下次轮询时正常检测
                result = {
                    'session_id': session_id,
                    'status': 'diagnosing',  # 给前端看的字符串标记
                    'mode': 'guided',
                    'collected_so_far': {
                        'symptoms': session.symptoms,
                        'duration': session.duration,
                        'medical_history': session.medical_history,
                        'medication_history': session.medication_history,
                        'scales': session.scales,
                    },
                    'collected_info': {
                        'symptoms': session.symptoms,
                        'duration': session.duration,
                        'medical_history': session.medical_history,
                        'medication_history': session.medication_history,
                        'scales': session.scales,
                    },
                }
                return result, response
            
            # 还在收集中，返回引导问题
            result = {
                'session_id': session_id,
                'status': session.status.value,
                'mode': state_update.get('mode', 'guided'),
                'collected_so_far': {
                    'symptoms': session.symptoms,
                    'duration': session.duration,
                    'medical_history': session.medical_history,
                    'medication_history': session.medication_history,
                    'scales': session.scales,
                },
                'next_question': session.current_question,
            }
            return result, response
        
        # 已经在诊断中或已完成
        elif session.status == SessionStatus.DIAGNOSING:
            # 如果已有诊断结果，直接返回
            if session.diagnosis_result:
                # ===== 修复：确保返回 collected_info，让右侧分数显示正常 =====
                result_with_collected = dict(session.diagnosis_result)
                result_with_collected['collected_info'] = {
                    'symptoms': session.symptoms,
                    'duration': session.duration,
                    'medical_history': session.medical_history,
                    'medication_history': session.medication_history,
                    'scales': session.scales,
                }
                return result_with_collected, self._generate_final_report(
                    session, session.diagnosis_result
                )
            
            # 运行诊断
            diagnosis_result = self._run_diagnosis(session)
            final_response = self._generate_final_report(
                session, diagnosis_result
            )
            # ===== 修复：确保返回 collected_info，让右侧分数显示正常 =====
            result_with_collected = dict(diagnosis_result)
            result_with_collected['collected_info'] = {
                'symptoms': session.symptoms,
                'duration': session.duration,
                'medical_history': session.medical_history,
                'medication_history': session.medication_history,
                'scales': session.scales,
            }
            return result_with_collected, final_response
        
        elif session.status == SessionStatus.COMPLETED:
            # 已完成：允许用户继续提问
            # 简单的规则回应
            user_msg = user_message.strip()
            
            # 常见问题回应
            if any(k in user_msg for k in ['怎么办', '怎么缓解', '怎么改善', '建议']):
                response = """关于如何改善，这里有几个小建议：

🌙 睡眠方面：尽量保持规律作息，睡前1小时放下手机，可以听听轻音乐。

🌿 情绪方面：不用强迫自己"马上好起来"，允许自己有状态不好的时候。可以把感受写下来，或者和信任的人聊聊。

🏃 身体方面：每天出门走10-15分钟，晒晒太阳，对情绪很有帮助。

💙 如果觉得状态持续不好，一定要去看专业的医生或心理咨询师，这很重要。

有什么具体的困扰想聊聊吗？"""
            
            elif any(k in user_msg for k in ['谢谢', '感谢', '多谢']):
                response = """不客气 💙

记住：你不是一个人在面对这些。如果状态不好的时候，随时可以再来聊聊，或者去找专业的帮助。

好好照顾自己。"""
            
            elif any(k in user_msg for k in ['活着', '不想活', '自杀', '死', '没意思']):
                response = """我能感受到你现在可能特别难熬 💙

有这样的想法并不奇怪，很多人在特别困难的时候都会有类似的念头。

但请你一定记得：
1. 这种感觉不是永久的，它会过去的
2. 你不是一个人，有人在乎你
3. 如果觉得撑不住了，立刻打心理援助热线，或者去医院急诊

中国心理危机干预热线：400-161-9995（24小时）
生命热线：400-821-1215

请一定一定，再给自己多一点点时间，好吗？"""
            
            else:
                # 默认回应
                response = f"""我收到你的消息了："{user_message}"

如果有什么具体的困扰想聊聊，或者想了解关于情绪、睡眠、就医建议等方面的内容，都可以告诉我 💙

记住，报告只是一个参考，最重要的是你自己的感受。"""
            
            return session.diagnosis_result, response
        
        # 默认情况
        return {'status': 'unknown'}, "正在处理您的请求..."
    
    def _run_diagnosis(self, session: SessionState) -> Dict[str, Any]:
        """运行完整诊断流程"""
        # 转换量表格式：从对话引导的字典格式 → scale_agent 期望的数字格式
        # 对话引导：{'PHQ9': {'score': 10, 'items': {...}}, 'GAD7': {...}}
        # scale_agent 期望：{'PHQ9': 10, 'GAD7': 8}
        
        # ===== 先把量表数据准备好，用于返回给前端（确保右侧显示分数） =====
        phq9_for_display = 0
        gad7_for_display = 0
        if isinstance(session.scales.get('PHQ9'), dict):
            phq9_for_display = session.scales['PHQ9'].get('score', 0)
        else:
            phq9_for_display = session.scales.get('PHQ9', 0)
            
        if isinstance(session.scales.get('GAD7'), dict):
            gad7_for_display = session.scales['GAD7'].get('score', 0)
        else:
            gad7_for_display = session.scales.get('GAD7', 0)
        
        scales_for_display = {
            'PHQ9': phq9_for_display,
            'GAD7': gad7_for_display
        }
        scale_answers_for_workflow = {}
        for key, value in session.scales.items():
            if isinstance(value, dict):
                # 从字典中提取分数
                scale_answers_for_workflow[key] = value.get('score', 0)
            else:
                scale_answers_for_workflow[key] = value
        
        # 准备工作流输入
        workflow_input = {
            'session_id': session.session_id,
            'text': ' '.join(session.patient_input),
            'age': getattr(session, 'age', None),
            'gender': getattr(session, 'gender', None),
            'scale_answers': scale_answers_for_workflow,
            'history': [],
        }
        
        # 运行诊断工作流
        state = self.diagnosis_workflow.invoke(workflow_input)
        
        # 保存诊断结果
        session.diagnosis_result = dict(state)
        session.agent_traces = state.get('agent_traces', [])
        session.status = SessionStatus.COMPLETED
        
        return dict(state)
    
    def _generate_final_report(self, session: SessionState, 
                             diagnosis_result: Dict[str, Any]) -> str:
        """生成最终诊断报告"""
        report = diagnosis_result.get('report', {})
        
        # 量表分数
        phq9_score = 0
        gad7_score = 0
        if isinstance(session.scales.get('PHQ9'), dict):
            phq9_score = session.scales['PHQ9'].get('score', 0)
        else:
            phq9_score = session.scales.get('PHQ9', 0)
            
        if isinstance(session.scales.get('GAD7'), dict):
            gad7_score = session.scales['GAD7'].get('score', 0)
        else:
            gad7_score = session.scales.get('GAD7', 0)
        
        # 构建报告
        lines = []
        lines.append("=" * 50)
        lines.append("📊 心理健康评估报告")
        lines.append("=" * 50)
        lines.append("")
        
        # 基本信息
        lines.append("【基本信息】")
        lines.append(f"  症状：{', '.join(session.symptoms) if session.symptoms else '无'}")
        lines.append(f"  持续时间：{session.duration or '未提供'}")
        lines.append("")
        
        # 量表分数
        lines.append("【量表评估结果】")
        phq9_level = self._get_phq9_level(phq9_score)
        gad7_level = self._get_gad7_level(gad7_score)
        lines.append(f"  PHQ-9（抑郁量表）：{phq9_score} 分 （{phq9_level}）")
        lines.append(f"  GAD-7（焦虑量表）：{gad7_score} 分 （{gad7_level}）")
        lines.append("")
        
        # 疑似诊断
        suspected = report.get('suspected_diagnosis', [])
        if suspected:
            lines.append("【疑似诊断】")
            for diag in suspected:
                lines.append(f"  • {diag}")
            lines.append("")
        
        # 风险等级
        risk_level = report.get('risk_level', '未知')
        lines.append(f"【风险等级】：{risk_level}")
        lines.append("")
        
        # 建议
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append("【就医建议】")
            for rec in recommendations:
                lines.append(f"  • {rec}")
            lines.append("")
        
        # 【新增】：个人生活建议
        lines.append("💡 给您的几点建议")
        lines.append("")
        lines.append("  🛌 关于睡眠：")
        lines.append("    • 尽量保持规律作息，每天同一时间入睡和起床")
        lines.append("    • 睡前1小时尽量不看手机，可以听听轻音乐或冥想")
        lines.append("    • 如果实在睡不着，不用强迫自己，起来做些轻松的事")
        lines.append("")
        lines.append("  🍎 关于饮食：")
        lines.append("    • 尽量按时吃饭，即使没有胃口也吃一点点")
        lines.append("    • 减少咖啡、浓茶的摄入，尤其是下午之后")
        lines.append("    • 多喝水，身体的状态会影响心情")
        lines.append("")
        lines.append("  🏃 关于活动：")
        lines.append("    • 每天出门走10-15分钟，哪怕只是下楼买个东西")
        lines.append("    • 阳光对情绪很有帮助，多晒晒太阳")
        lines.append("    • 做一些简单的运动，比如散步、拉伸")
        lines.append("")
        lines.append("  💭 关于心情：")
        lines.append("    • 心情不好的时候，不用强迫自己'振作起来'")
        lines.append("    • 允许自己有状态不好的时候，这很正常")
        lines.append("    • 和信任的人聊聊，或者写下来，都会好一些")
        lines.append("")
        lines.append("  🌻 最重要的：")
        lines.append("    • 你不是一个人在面对这些")
        lines.append("    • 如果觉得自己扛不住了，一定要寻求专业帮助")
        lines.append("")
        
        # 安全声明
        lines.append("⚠️  重要声明：")
        lines.append("  本评估仅供筛查参考，不构成医学诊断。")
        lines.append("  如有需要，请前往正规医院精神科/心理科就诊。")
        lines.append("")
        lines.append("=" * 50)
        lines.append("")
        lines.append("💬 如果您想聊聊具体的感受，或者有什么问题，随时可以告诉我。")
        
        return '\n'.join(lines)
    
    def quick_diagnosis(self, session_id: str, text: str, 
                       scale_answers: Dict[str, int],
                       age: str = None, gender: str = None) -> Tuple[Dict[str, Any], str]:
        """
        快速诊断模式 - 直接输入症状和量表分数
        
        Args:
            session_id: 会话ID
            text: 症状描述
            scale_answers: 量表分数字典 {'PHQ9': 16, 'GAD7': 10}
            age: 年龄
            gender: 性别
        """
        session = self.session_manager.create_session(session_id)
        session.add_input(text)
        session.scales = dict(scale_answers)
        session.status = SessionStatus.DIAGNOSING
        
        if age:
            session.age = age
        if gender:
            session.gender = gender
        
        # 提取症状
        from app.agents.dialogue_agent import DialogueGuideAgent
        symptoms = DialogueGuideAgent()._extract_symptoms(text)
        for symptom in symptoms:
            session.add_symptom(symptom)
        
        # 运行诊断
        diagnosis_result = self._run_diagnosis(session)
        final_response = self._generate_final_report(session, diagnosis_result)
        
        return diagnosis_result, final_response
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {'exists': False}
        
        return {
            'exists': True,
            'session_id': session.session_id,
            'status': session.status.value,
            'symptoms': session.symptoms,
            'duration': session.duration,
            'medical_history': session.medical_history,
            'medication_history': session.medication_history,
            'scales': session.scales,
            'questions_asked': session.questions_asked,
        }
    
    def reset_session(self, session_id: str):
        """重置会话"""
        self.session_manager.delete_session(session_id)


# 全局单例
_orchestrator_v2 = None


def get_orchestrator_v2() -> DiagnosisOrchestratorV2:
    """获取 V2 编排器单例"""
    global _orchestrator_v2
    if _orchestrator_v2 is None:
        _orchestrator_v2 = DiagnosisOrchestratorV2()
    return _orchestrator_v2
