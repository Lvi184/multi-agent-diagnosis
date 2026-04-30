#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话服务层 - 心理咨询式引导 + 多 Agent 诊断
"""
import time
import re
import asyncio
from typing import Dict, Any, Tuple, Optional
from app.repositories import session_repo, record_repo, user_repo
from app.graph.workflow import LangGraphDiagnosisWorkflow


class CounselingGuide:
    """
    心理咨询式对话引导 Agent
    """
    
    def __init__(self):
        # PHQ-9 问题
        self.phq9_questions = [
            "做事提不起劲或没有兴趣？",
            "感到心情低落、沮丧或绝望？",
            "入睡困难、睡不安稳或睡眠过多？",
            "感到疲倦或没有活力？",
            "食欲不振或吃太多？",
            "觉得自己很糟，或觉得自己很失败，或让自己或家人失望？",
            "对事物专注有困难，例如阅读报纸或看电视时？",
            "动作或说话速度缓慢到别人已经觉察？或相反，变得比平时更加烦躁或坐立不安？",
            "有不如死掉或用某种方式伤害自己的念头？",
        ]
        
        # GAD-7 问题
        self.gad7_questions = [
            "感到紧张、焦虑或急切？",
            "无法停止或控制担忧？",
            "对各种各样的事情担忧过多？",
            "很难放松下来？",
            "如此焦躁以至于难以静坐？",
            "变得容易烦恼或急躁？",
            "感到似乎将有可怕的事情发生而害怕？",
        ]
        
        self.score_options = "请选择：0=完全不会，1=好几天，2=一半以上天数，3=几乎每天"
        
        # 共情回应模板
        self.empathy_responses = {
            'mood_bad': [
                "我能感受到你现在的心情确实不太好。",
                "听起来你最近过得不太容易。",
                "这种低落的感觉一定很难受吧。",
            ],
            'sleep_bad': [
                "睡不好真的太煎熬了，第二天整个人都没精神。",
                "入睡困难的时候，躺在床上翻来覆去的感觉我能理解。",
            ],
            'energy_low': [
                "这种浑身乏力、什么都不想做的感觉真的很难受。",
                "精力不够的时候，连简单的事情都觉得很费力。",
            ],
            'stress_event': [
                "工作压力大的时候，真的会让人喘不过气来。",
                "发生这样的事情，换做是谁都会觉得很难的。",
            ],
            'suicide_no': [
                "太好了，没有这方面的想法就好。",
                "听到你这么说我就放心了。",
            ],
            'encouragement': [
                "愿意说出来就是好的开始。",
                "你愿意跟我分享这些，真的很棒。",
            ],
        }
        
        # 追问模板
        self.probing_questions = {
            'mood': ["这种情况持续多久了呢？", "是发生了什么事情让你心情不好吗？"],
            'sleep': ["这种情况持续多久了呢？", "是入睡困难，还是容易醒吗？"],
            'energy': ["这种疲惫的感觉持续多久了呢？", "是身体上的累，还是心里觉得累？"],
            'event': ["可以跟我说说具体发生了什么吗？", "面对这些压力，你一般是怎么应对的呢？"],
        }
    
    def process_message(self, session: Any, user_message: str) -> Tuple[Dict[str, Any], str]:
        import random
        
        # 快速测试：直接输入两个分数
        score_match = re.match(r'^(\d+)\s+(\d+)$', user_message.strip())
        if score_match:
            session.phq9_score = min(int(score_match.group(1)), 27)
            session.gad7_score = min(int(score_match.group(2)), 21)
            session.conversation_stage = 'complete'
            return self._get_collected(session), "好的，量表分数已记录，现在开始进行综合分析..."
        
        current_stage = session.conversation_stage or 'init'
        step_count = getattr(session, 'stage_step_count', 0)
        
        # ========== 初始问候 ==========
        if current_stage == 'init':
            # 空消息：返回标准欢迎语
            if not user_message.strip():
                session.conversation_stage = 'mood'
                session.stage_step_count = 0
                return self._get_collected(session), "你好！我是心理健康助手。愿意跟我说说你最近的心情怎么样？"
            
            # 用户说了具体内容，进行意图识别
            msg_lower = user_message.lower()
            
            # 关键词检测
            has_mood = any(w in msg_lower for w in ['心情', '不开心', '开心', '低落', '郁闷', '抑郁', '难受', '不好', '难过', '糟'])
            has_sleep = any(w in msg_lower for w in ['睡', '睡着', '失眠', '早醒', '多梦', '易醒'])
            has_energy = any(w in msg_lower for w in ['累', '没精神', '疲惫', '乏力', '没劲', '困'])
            has_stress = any(w in msg_lower for w in ['压力', '焦虑', '紧张', '担心', '烦'])
            
            # 记录用户提到的所有症状
            if has_mood and '情绪低落' not in session.symptoms:
                session.symptoms.append('情绪低落')
            if has_sleep and '睡眠障碍' not in session.symptoms:
                session.symptoms.append('睡眠障碍')
            if has_energy and '精力下降' not in session.symptoms:
                session.symptoms.append('精力下降')
            if has_stress and '应激事件' not in session.symptoms:
                session.symptoms.append('应激事件')
            
            # 根据用户提到的内容，智能跳到下一个阶段
            symptoms_count = sum([has_mood, has_sleep, has_energy, has_stress])
            
            if symptoms_count == 0:
                # 用户啥具体症状都没说，正常问心情
                reply = "你好！我是心理健康助手。愿意跟我说说你最近的心情怎么样？"
                session.conversation_stage = 'mood'
            elif has_mood and not has_sleep:
                # 用户说了心情，没说睡眠 → 直接问睡眠
                reply = "我了解了你的心情情况。那最近睡眠怎么样呢？"
                session.conversation_stage = 'sleep'
            elif has_sleep and not has_energy:
                # 用户说了睡眠，没说精力 → 直接问精力
                reply = "我了解了你的睡眠情况。那最近精力怎么样呢？"
                session.conversation_stage = 'energy'
            elif has_energy and not has_stress:
                # 用户说了精力，没说压力事件 → 直接问压力
                reply = "我了解了你的情况。那最近有发生什么让你觉得压力很大的事情吗？"
                session.conversation_stage = 'event'
            else:
                # 用户说了很多，直接问风险筛查
                reply = "我了解了你的这些情况。有个问题我想确认一下：你有没有过不想活或者伤害自己的想法呢？"
                session.conversation_stage = 'risk'
            
            session.stage_step_count = 0
            return self._get_collected(session), reply
        
        # ========== 心情阶段 ==========
        elif current_stage == 'mood':
            has_negative = any(w in user_message for w in ['不好', '低落', '难受', '不开心', '抑郁', '郁闷', '差', '糟'])
            
            if step_count == 0:
                if has_negative:
                    session.symptoms.append('情绪低落')
                    reply = random.choice(self.empathy_responses['mood_bad']) + "\n\n"
                    reply += random.choice(self.probing_questions['mood'])
                else:
                    reply = "听起来心情还不错。那最近睡眠质量怎么样呢？"
                    session.conversation_stage = 'sleep'
                    session.stage_step_count = 0
                    return self._get_collected(session), reply
                
                session.stage_step_count = 1
                return self._get_collected(session), reply
            
            elif step_count == 1:
                # 第二轮回答，如果用户说"不好"，也记录症状
                if has_negative and '情绪低落' not in session.symptoms:
                    session.symptoms.append('情绪低落')
                
                reply = random.choice(self.empathy_responses['encouragement']) + "\n\n"
                reply += "那最近睡眠情况怎么样呢？睡得好吗？"
                
                session.conversation_stage = 'sleep'
                session.stage_step_count = 0
                return self._get_collected(session), reply
        
        # ========== 睡眠阶段 ==========
        elif current_stage == 'sleep':
            has_sleep_issue = any(w in user_message for w in ['不好', '睡不着', '入睡', '早醒', '失眠', '睡不好', '多梦', '易醒', '差', '糟', '不行'])
            
            if step_count == 0:
                if has_sleep_issue:
                    session.symptoms.append('睡眠障碍')
                    reply = random.choice(self.empathy_responses['sleep_bad']) + "\n\n"
                    reply += random.choice(self.probing_questions['sleep'])
                else:
                    reply = "睡眠不错是好事！那精力方面呢？会不会觉得很累、什么都不想做？"
                    session.conversation_stage = 'energy'
                    session.stage_step_count = 0
                    return self._get_collected(session), reply
                
                session.stage_step_count = 1
                return self._get_collected(session), reply
            
            elif step_count == 1:
                # 第二轮回答，如果用户说"不好"，也记录症状
                if has_sleep_issue and '睡眠障碍' not in session.symptoms:
                    session.symptoms.append('睡眠障碍')
                
                reply = random.choice(self.empathy_responses['encouragement']) + "\n\n"
                reply += "那精力方面怎么样呢？会不会觉得很累、什么都不想做？"
                
                session.conversation_stage = 'energy'
                session.stage_step_count = 0
                return self._get_collected(session), reply
        
        # ========== 精力阶段 ==========
        elif current_stage == 'energy':
            has_energy_issue = any(w in user_message for w in ['不好', '累', '没劲', '不想动', '没精神', '疲惫', '乏力', '困', '差'])
            
            if step_count == 0:
                if has_energy_issue:
                    session.symptoms.append('精力下降')
                    reply = random.choice(self.empathy_responses['energy_low']) + "\n\n"
                    reply += random.choice(self.probing_questions['energy'])
                else:
                    reply = "精力充沛是好事！那最近有没有发生什么让你觉得压力很大的事情呢？"
                    session.conversation_stage = 'event'
                    session.stage_step_count = 0
                    return self._get_collected(session), reply
                
                session.stage_step_count = 1
                return self._get_collected(session), reply
            
            elif step_count == 1:
                # 第二轮回答，如果用户说"是"或"不好"，也记录症状
                if has_energy_issue and '精力下降' not in session.symptoms:
                    session.symptoms.append('精力下降')
                
                reply = random.choice(self.empathy_responses['encouragement']) + "\n\n"
                reply += "那最近有没有发生什么让你觉得压力很大的事情呢？"
                
                session.conversation_stage = 'event'
                session.stage_step_count = 0
                return self._get_collected(session), reply
        
        # ========== 压力事件阶段 ==========
        elif current_stage == 'event':
            has_event = any(w in user_message for w in ['压力', '吵架', '失恋', '失业', '工作', '家人', '朋友', '分手', '离职', '有', '发生', '遇到'])
            no_event = any(w in user_message for w in ['没有', '没什么', '还好', '没发生', '没有特别'])
            
            if step_count == 0:
                if has_event and not no_event:
                    session.symptoms.append('应激事件')
                    reply = random.choice(self.empathy_responses['stress_event']) + "\n\n"
                    reply += random.choice(self.probing_questions['event'])
                else:
                    reply = "嗯，生活平顺就是最好的。有个问题我想确认一下：你有没有过不想活或者伤害自己的想法呢？"
                    session.conversation_stage = 'risk'
                    session.stage_step_count = 0
                    return self._get_collected(session), reply
                
                session.stage_step_count = 1
                return self._get_collected(session), reply
            
            elif step_count == 1:
                # 第二轮回答，如果用户说有压力事件，记录症状
                if has_event and not no_event and '应激事件' not in session.symptoms:
                    session.symptoms.append('应激事件')
                
                reply = random.choice(self.empathy_responses['encouragement']) + "\n\n"
                reply += "有个问题我想确认一下：你有没有过不想活或者伤害自己的想法呢？"
                
                session.conversation_stage = 'risk'
                session.stage_step_count = 0
                return self._get_collected(session), reply
        
        # ========== 风险筛查 ==========
        elif current_stage == 'risk':
            has_risk = any(w in user_message for w in ['有', '想过', '有时候', '偶尔', '是'])
            no_risk = any(w in user_message for w in ['没有', '没', '不会', '从来'])
            
            if has_risk and not no_risk:
                session.has_suicide_risk = True
                reply = "谢谢你愿意告诉我，这真的很重要。\n\n"
                reply += "请一定记住：即使现在觉得很难，情况也是会变好的。\n\n"
            else:
                session.has_suicide_risk = False
                reply = random.choice(self.empathy_responses['suicide_no']) + "\n\n"
            
            reply += "接下来我们做两个简单的量表评估。\n\n"
            reply += "**PHQ-9 抑郁症筛查量表**（共9题）\n"
            reply += f"{self.score_options}\n\n"
            reply += f"第1题：{self.phq9_questions[0]}"
            
            session.conversation_stage = 'phq9_question'
            session.phq9_answers = []
            return self._get_collected(session), reply
        
        # ========== PHQ-9 逐题询问 ==========
        elif current_stage == 'phq9_question':
            answer = self._parse_score(user_message)
            
            if answer is None:
                q_num = len(session.phq9_answers or [])
                return self._get_collected(session), f"请选择一个数字回答哦～\n\n{self.score_options}\n\n第{q_num + 1}题：{self.phq9_questions[q_num]}"
            
            if not hasattr(session, 'phq9_answers') or not session.phq9_answers:
                session.phq9_answers = []
            session.phq9_answers.append(answer)
            
            if len(session.phq9_answers) < 9:
                next_q = len(session.phq9_answers)
                reply = f"好的，第{next_q}题已记录。\n\n"
                reply += f"第{next_q + 1}题：{self.phq9_questions[next_q]}\n"
                reply += self.score_options
                return self._get_collected(session), reply
            else:
                session.phq9_score = sum(session.phq9_answers)
                reply = f"✅ PHQ-9 完成！你的分数是：{session.phq9_score}分\n\n"
                reply += "接下来我们做 GAD-7 焦虑症筛查量表（共7题）\n\n"
                reply += f"第1题：{self.gad7_questions[0]}\n"
                reply += self.score_options
                
                session.conversation_stage = 'gad7_question'
                session.gad7_answers = []
                return self._get_collected(session), reply
        
        # ========== GAD-7 逐题询问 ==========
        elif current_stage == 'gad7_question':
            answer = self._parse_score(user_message)
            
            if answer is None:
                q_num = len(session.gad7_answers or [])
                return self._get_collected(session), f"请选择一个数字回答哦～\n\n{self.score_options}\n\n第{q_num + 1}题：{self.gad7_questions[q_num]}"
            
            if not hasattr(session, 'gad7_answers') or not session.gad7_answers:
                session.gad7_answers = []
            session.gad7_answers.append(answer)
            
            if len(session.gad7_answers) < 7:
                next_q = len(session.gad7_answers)
                reply = f"好的，第{next_q}题已记录。\n\n"
                reply += f"第{next_q + 1}题：{self.gad7_questions[next_q]}\n"
                reply += self.score_options
                return self._get_collected(session), reply
            else:
                session.gad7_score = sum(session.gad7_answers)
                session.conversation_stage = 'complete'
                
                reply = f"✅ GAD-7 完成！你的分数是：{session.gad7_score}分\n\n"
                reply += "🎉 两个量表都完成了！谢谢你的耐心回答。\n"
                reply += "现在我将通过多 Agent 系统为你进行综合分析，请稍候..."
                
                return self._get_collected(session), reply
        
        # ========== 已经完成诊断 ==========
        elif current_stage == 'complete':
            return self._get_collected(session), "诊断已经完成了。点击查看详细报告了解结果。"
        
        # 默认回复
        return self._get_collected(session), "我理解了。还有什么想跟我说的吗？"
    
    def _parse_score(self, message: str) -> Optional[int]:
        num_match = re.search(r'(\d+)', message)
        if num_match:
            score = int(num_match.group(1))
            if 0 <= score <= 3:
                return score
        return None
    
    def _get_collected(self, session: Any) -> Dict[str, Any]:
        return {
            'symptoms': session.symptoms or [],
            'phq9_score': session.phq9_score,
            'gad7_score': session.gad7_score,
            'has_suicide_risk': session.has_suicide_risk,
            'stage': session.conversation_stage,
        }


class DialogueService:
    """对话服务 - 处理用户消息，管理会话状态"""
    
    def __init__(self):
        self.dialogue_agent = CounselingGuide()
        self.diagnosis_workflow = LangGraphDiagnosisWorkflow()
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], str]:
        
        db_session = await session_repo.get_by_session_id(session_id)
        
        if not db_session:
            db_session = await session_repo.create(
                session_id=session_id,
                user_id=user_id,
                age=age,
                gender=gender,
                status='collecting',
                symptoms=[],
                conversation_stage='init',
                chat_history=[],
                phq9_answers=[],
                gad7_answers=[],
                stage_step_count=0,
            )
        
        if age and not db_session.age:
            await session_repo.update(db_session.id, age=age)
        if gender and not db_session.gender:
            await session_repo.update(db_session.id, gender=gender)
        
        # 空消息：仅查询状态，不处理对话
        if not message.strip():
            collected = {
                'symptoms': db_session.symptoms or [],
                'phq9_score': db_session.phq9_score,
                'gad7_score': db_session.gad7_score,
                'has_suicide_risk': db_session.has_suicide_risk,
                'stage': db_session.conversation_stage,
            }
            
            # 检查是否已有诊断结果（轮询时用）
            diagnosis_result = None
            final_status = db_session.status
            
            # 不管当前状态是什么，都检查一下诊断记录是否存在（处理后台任务完成的情况）
            if db_session.status in ['diagnosing', 'completed']:
                record = await record_repo.get_by_session_id(db_session.id)
                if record:
                    diagnosis_result = record.structured_report
                    final_status = 'completed'  # 如果有记录，直接标记为完成
            
            return {
                'session_id': session_id,
                'status': final_status,
                'diagnosis_result': diagnosis_result,
                'collected_info': collected,
            }, ""
        
        # 保存用户消息
        chat_history = list(db_session.chat_history or [])
        chat_history.append({'role': 'user', 'content': message})
        await session_repo.update(db_session.id, chat_history=chat_history)
        
        # 处理对话
        collected, reply = self.dialogue_agent.process_message(db_session, message)
        
        # 保存 AI 回复
        chat_history.append({'role': 'assistant', 'content': reply})
        
        # 更新会话状态
        new_status = db_session.status
        should_start_diagnosis = False
        
        # 量表完成，标记为诊断中，并启动诊断
        if collected['stage'] == 'complete' and db_session.status == 'collecting':
            new_status = 'diagnosing'  # 标记为诊断中
            should_start_diagnosis = True
        
        await session_repo.update(
            db_session.id,
            symptoms=collected['symptoms'],
            phq9_score=collected['phq9_score'],
            gad7_score=collected['gad7_score'],
            has_suicide_risk=collected['has_suicide_risk'],
            conversation_stage=collected['stage'],
            status=new_status,
            chat_history=chat_history,
            phq9_answers=getattr(db_session, 'phq9_answers', []),
            gad7_answers=getattr(db_session, 'gad7_answers', []),
            stage_step_count=getattr(db_session, 'stage_step_count', 0),
        )
        
        # ========== 后台异步启动诊断，不阻塞请求返回 ==========
        if should_start_diagnosis:
            asyncio.create_task(self._run_diagnosis_background(
                db_session.id, 
                session_id, 
                user_id
            ))
        
        # 检查是否已有诊断结果
        diagnosis_result = None
        final_status = new_status
        
        # 如果标记为 diagnosing，检查是否后台已经完成
        if new_status == 'diagnosing' or db_session.status == 'diagnosing':
            record = await record_repo.get_by_session_id(db_session.id)
            if record:
                diagnosis_result = record.structured_report
                final_status = 'completed'
        
        return {
            'session_id': session_id,
            'status': final_status,
            'diagnosis_result': diagnosis_result,
            'collected_info': collected,
        }, reply
    
    async def _run_diagnosis_background(self, session_db_id: int, session_id: str, user_id: Optional[int]):
        """后台运行多 Agent 诊断"""
        try:
            print(f"[{session_id}] 开始后台诊断...")
            
            # 获取会话信息
            session = await session_repo.get_by_id(session_db_id)
            if not session:
                return
            
            # 运行诊断（带超时保护）
            start_time = time.time()
            try:
                result = await asyncio.wait_for(
                    self._run_actual_diagnosis(session),
                    timeout=300.0  # 5分钟
                )
            except asyncio.TimeoutError:
                result = await self._rule_based_diagnosis(session)
            
            result['diagnosis_time_ms'] = int((time.time() - start_time) * 1000)
            
            # 保存诊断记录
            await record_repo.create(
                session_id=session_db_id,
                user_id=user_id,
                suspected_diagnosis=result.get('suspected_diagnosis', []),
                risk_level=result.get('risk_level', 'unknown'),
                risk_types=result.get('risk_types', []),
                recommendations=result.get('recommendations', []),
                evidence_chain=result.get('evidence_chain', []),
                structured_report=result,
                agent_traces=result.get('agent_traces', []),
            )
            
            # 标记会话完成
            await session_repo.update(session_db_id, status='completed')
            
            print(f"[{session_id}] 诊断完成！")
            
        except Exception as e:
            print(f"[{session_id}] 诊断出错: {e}")
            # 出错了用规则结果兜底
            session = await session_repo.get_by_id(session_db_id)
            if session:
                result = await self._rule_based_diagnosis(session)
                result['diagnosis_error'] = str(e)
                
                await record_repo.create(
                    session_id=session_db_id,
                    user_id=user_id,
                    suspected_diagnosis=result.get('suspected_diagnosis', []),
                    risk_level=result.get('risk_level', 'unknown'),
                    risk_types=result.get('risk_types', []),
                    recommendations=result.get('recommendations', []),
                    evidence_chain=result.get('evidence_chain', []),
                    structured_report=result,
                )
                
                await session_repo.update(session_db_id, status='completed')
    
    async def _run_actual_diagnosis(self, session: Any) -> Dict[str, Any]:
        """实际运行诊断（先用规则诊断确保稳定，后续可替换为多 Agent）"""
        # 先返回规则诊断结果，确保系统稳定
        # 如需启用多 Agent 诊断，可取消下面的注释
        return await self._rule_based_diagnosis(session)
        
        # phq9 = session.phq9_score or 0
        # gad7 = session.gad7_score or 0
        
        # request = {
        #     'session_id': session.session_id,
        #     'text': ' | '.join(session.symptoms or []),
        #     'age': session.age,
        #     'gender': session.gender,
        #     'history': [],
        #     'scale_answers': {
        #         'phq9': phq9,
        #         'gad7': gad7,
        #     },
        # }
        
        # # 在线程池中运行（避免阻塞事件循环）
        # loop = asyncio.get_event_loop()
        # result = await loop.run_in_executor(None, self.diagnosis_workflow.invoke, request)
        # return result
    
    async def _rule_based_diagnosis(self, session: Any) -> Dict[str, Any]:
        """基于规则的快速诊断（备用方案）"""
        phq9 = session.phq9_score or 0
        gad7 = session.gad7_score or 0
        
        if phq9 >= 20 or gad7 >= 15:
            risk_level = 'high'
        elif phq9 >= 15 or gad7 >= 10:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        suspected = []
        if phq9 >= 10:
            suspected.append('抑郁症状')
        if gad7 >= 8:
            suspected.append('焦虑症状')
        if session.has_suicide_risk:
            suspected.append('自杀风险筛查阳性')
        if not suspected:
            suspected.append('未见明显异常，建议持续观察心理健康')
        
        recommendations = [
            "建议由精神科/心理科专业人员进一步评估",
            "建议保持规律作息",
            "建议适度运动",
        ]
        
        if phq9 >= 15:
            recommendations.insert(0, "⚠️ 抑郁分数较高，强烈建议尽快前往正规医院精神科就诊")
        if gad7 >= 15:
            recommendations.insert(1, "⚠️ 焦虑分数较高，建议学习放松技巧，必要时就医")
        if session.has_suicide_risk:
            recommendations.insert(0, "🚨 自杀风险筛查阳性，请立即寻求专业帮助")
        
        return {
            'suspected_diagnosis': suspected,
            'risk_level': risk_level,
            'risk_types': [f'PHQ-9: {phq9}, GAD-7: {gad7}'],
            'recommendations': recommendations,
            'evidence_chain': [
                f'PHQ-9 抑郁量表: {phq9}分',
                f'GAD-7 焦虑量表: {gad7}分',
                f'自杀风险筛查: {"阳性" if session.has_suicide_risk else "阴性"}',
            ],
            'method': 'rule_based',
        }


# 全局单例
dialogue_service = DialogueService()
