from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.orchestrator import DiagnosisOrchestrator
from app.core.orchestrator_v2 import get_orchestrator_v2
from app.graph.workflow import build_diagnosis_graph
from app.schemas.diagnosis import ChatRequest, ChatResponse, DiagnosisRequest, DiagnosisResponse
from app.agents.intent_classifier import get_intent_classifier, IntentType

router = APIRouter()
orchestrator = DiagnosisOrchestrator()
orchestrator_v2 = get_orchestrator_v2()


class DialogueRequest(BaseModel):
    """对话请求 - 支持多轮对话"""
    session_id: str
    message: str
    age: Optional[int] = None
    gender: Optional[str] = None
    scale_answers: Optional[Dict[str, Any]] = None


class DialogueResponse(BaseModel):
    """对话响应"""
    session_id: str
    status: str
    mode: str  # 'quick' | 'guided'
    reply: str
    collected_info: Optional[Dict[str, Any]] = None
    diagnosis_result: Optional[Dict[str, Any]] = None
    is_completed: bool = False


@router.get('/health')
def health():
    return {
        'status': 'ok',
        'service': settings.app_name,
        'version': settings.app_version,
        'llm_provider': settings.llm_provider,
        'deepseek_configured': bool(settings.deepseek_api_key),
    }


@router.post('/diagnose', response_model=DiagnosisResponse)
def diagnose(request: DiagnosisRequest):
    """原有的单轮诊断接口"""
    return orchestrator.run(request)


@router.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    单轮对话接口 - 带前置意图判断
    
    优化：
    1. 先进行意图分类，避免非诊断场景强制走完整流程
    2. 简单问候、闲聊等直接回复，不进入10个Agent流程
    3. 只有真正的症状报告才执行完整诊断
    """
    intent_classifier = get_intent_classifier()
    
    # 1. 前置意图判断
    intent, confidence = intent_classifier.classify(request.message)
    
    # 2. 检查是否有预填写的量表分数（有分数直接进入诊断）
    has_scale_scores = False
    if request.scale_answers:
        phq9 = request.scale_answers.get('PHQ9', 0)
        gad7 = request.scale_answers.get('GAD7', 0)
        if phq9 > 0 or gad7 > 0:
            has_scale_scores = True
    
    # 3. 非诊断意图，直接回复（除非有量表分数）
    if not has_scale_scores and not intent_classifier.should_enter_diagnosis(intent):
        reply = intent_classifier.get_response(intent)
        return ChatResponse(
            session_id=request.session_id, 
            reply=reply, 
            report=None,
            intent={'type': intent, 'confidence': confidence}
        )
    
    # 4. 真正的诊断请求，执行完整流程
    diagnosis_request = DiagnosisRequest(
        session_id=request.session_id,
        text=request.message,
        age=request.age,
        gender=request.gender,
        scale_answers=request.scale_answers,
        history=request.history,
    )
    report = orchestrator.run(diagnosis_request)
    reply = (
        f"我已完成本轮多Agent辅助筛查。疑似方向：{'、'.join(report.suspected_diagnosis)}；"
        f"风险等级：{report.risk_level}。{report.safety_message}"
    )
    if report.recommendations:
        reply += ' 建议：' + '；'.join(report.recommendations[:2])
    return ChatResponse(
        session_id=request.session_id, 
        reply=reply, 
        report=report,
        intent={'type': intent, 'confidence': confidence}
    )


@router.post('/dialogue', response_model=DialogueResponse)
def dialogue(request: DialogueRequest):
    """
    【新】多轮对话诊断接口 - 支持两种模式
    
    模式一：引导评估模式（无量表分数）
      - Agent 会逐步引导患者完成信息采集
      - 自动完成 PHQ-9 / GAD-7 量表
      - 收集完成后自动执行诊断
    
    模式二：快速诊断模式（已有量表分数）
      - 直接输入症状 + 量表分数
      - 立即执行完整诊断流程
    
    使用方法：
    1. 第一轮发送消息即可，无需其他参数
    2. 后续每轮回复发送 answer 即可
    3. 系统自动判断收集进度，完成后返回诊断结果
    """
    # 使用 V2 编排器处理
    result, reply = orchestrator_v2.process_message(
        session_id=request.session_id,
        user_message=request.message,
        scale_answers=request.scale_answers,
        age=request.age,
        gender=request.gender,
    )
    
    # 判断是否完成
    is_completed = result.get('status') == 'completed' or result.get('report') is not None
    
    return DialogueResponse(
        session_id=request.session_id,
        status=result.get('status', 'processing'),
        mode=result.get('mode', 'guided'),
        reply=reply,
        collected_info=result.get('collected_so_far'),
        diagnosis_result=result if is_completed else None,
        is_completed=is_completed,
    )


@router.get('/session/{session_id}')
def get_session_info(session_id: str):
    """获取会话状态信息"""
    info = orchestrator_v2.get_session_info(session_id)
    return info


@router.delete('/session/{session_id}')
def reset_session(session_id: str):
    """重置/删除会话"""
    orchestrator_v2.reset_session(session_id)
    return {'status': 'ok', 'message': f'会话 {session_id} 已重置'}


@router.get('/graph/mermaid')
def graph_mermaid():
    graph = build_diagnosis_graph()
    try:
        return {'mermaid': graph.get_graph().draw_mermaid()}
    except Exception as exc:
        return {'error': str(exc), 'message': '当前LangGraph版本不支持draw_mermaid或缺少可视化依赖。'}
