from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    session_id: str = 'web-session'
    text: str
    age: Optional[int] = None
    gender: Optional[str] = None
    scale_answers: Dict[str, int] = Field(default_factory=dict)
    history: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str = 'web-session'
    message: str
    age: Optional[int] = None
    gender: Optional[str] = None
    scale_answers: Dict[str, int] = Field(default_factory=dict)
    history: List[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    agent: str
    summary: str
    output: Dict[str, Any] = Field(default_factory=dict)


class DiagnosisResponse(BaseModel):
    session_id: str
    suspected_diagnosis: List[str]
    risk_level: str
    risk_types: List[str]
    evidence_chain: List[str]
    recommendations: List[str]
    safety_message: str
    structured_report: Dict[str, Any]
    agent_traces: List[AgentTrace]


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    report: Optional[DiagnosisResponse] = None
    intent: Optional[Dict[str, Any]] = None
