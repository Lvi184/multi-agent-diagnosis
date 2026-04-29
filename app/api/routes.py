from fastapi import APIRouter

from app.core.config import settings
from app.core.orchestrator import DiagnosisOrchestrator
from app.graph.workflow import build_diagnosis_graph
from app.schemas.diagnosis import ChatRequest, ChatResponse, DiagnosisRequest, DiagnosisResponse

router = APIRouter()
orchestrator = DiagnosisOrchestrator()


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
    return orchestrator.run(request)


@router.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
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
    return ChatResponse(session_id=request.session_id, reply=reply, report=report)


@router.get('/graph/mermaid')
def graph_mermaid():
    graph = build_diagnosis_graph()
    try:
        return {'mermaid': graph.get_graph().draw_mermaid()}
    except Exception as exc:
        return {'error': str(exc), 'message': '当前LangGraph版本不支持draw_mermaid或缺少可视化依赖。'}
