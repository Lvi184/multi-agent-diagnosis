from app.graph.workflow import LangGraphDiagnosisWorkflow
from app.schemas.diagnosis import AgentTrace, DiagnosisResponse


class DiagnosisOrchestrator:
    """Compatibility wrapper around the LangGraph workflow.

    Existing FastAPI routes can keep calling ``DiagnosisOrchestrator.run`` while
    the actual multi-agent execution is now handled by LangGraph StateGraph.
    """

    def __init__(self):
        self.workflow = LangGraphDiagnosisWorkflow()

    def run(self, request):
        state = self.workflow.invoke(request)
        report = state.get("report", {})
        traces = [AgentTrace(**trace) for trace in state.get("agent_traces", [])]
        return DiagnosisResponse(
            session_id=request.session_id,
            agent_traces=traces,
            **report,
        )
