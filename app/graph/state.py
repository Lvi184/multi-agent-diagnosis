from typing import Any, Dict, List, Optional, TypedDict


class DiagnosisState(TypedDict, total=False):
    """Shared LangGraph state for the multi-agent psychiatric workflow.

    Each node reads selected keys and returns a partial update. The state is kept
    JSON-serializable so it can be returned by FastAPI, persisted, or inspected
    during experiments.
    """

    session_id: str
    text: str
    age: Optional[int]
    gender: Optional[str]
    history: List[str]
    scale_answers: Dict[str, int]

    intake: Dict[str, Any]
    structured: Dict[str, Any]
    scales: Dict[str, Any]
    diagnosis: Dict[str, Any]
    model_verification: Dict[str, Any]
    knowledge: Dict[str, Any]
    differential: Dict[str, Any]
    risk: Dict[str, Any]
    validation: Dict[str, Any]
    report: Dict[str, Any]

    current_step: str
    next_action: str
    errors: List[str]
    agent_traces: List[Dict[str, Any]]
