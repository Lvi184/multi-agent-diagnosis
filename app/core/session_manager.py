#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理器 - 实现多轮对话记忆与状态管理
"""
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class SessionStatus(Enum):
    """会话状态枚举"""
    INIT = "init"                      # 初始状态
    COLLECTING_SYMPTOMS = "collecting_symptoms"    # 采集症状中
    COLLECTING_SCALE = "collecting_scale"          # 量表评估中
    DIAGNOSING = "diagnosing"            # 诊断中
    COMPLETED = "completed"              # 已完成


@dataclass
class SessionState:
    """会话状态数据结构"""
    session_id: str
    status: SessionStatus
    created_at: float
    updated_at: float
    patient_input: List[str] = None      # 患者历史输入
    symptoms: List[str] = None           # 已收集的症状
    duration: str = ""                    # 持续时间
    severity: str = ""                    # 严重程度
    medical_history: str = ""             # 既往史
    medication_history: str = ""          # 用药史
    suicide_risk_clues: List[str] = None  # 自杀风险线索
    
    # 量表分数
    scales: Dict[str, Any] = None
    
    # 诊断结果
    diagnosis_result: Dict[str, Any] = None
    
    # Agent 执行轨迹
    agent_traces: List[Dict[str, Any]] = None
    
    # 当前追问问题
    current_question: str = ""
    questions_asked: int = 0
    
    def __post_init__(self):
        if self.patient_input is None:
            self.patient_input = []
        if self.symptoms is None:
            self.symptoms = []
        if self.suicide_risk_clues is None:
            self.suicide_risk_clues = []
        if self.scales is None:
            self.scales = {}
        if self.agent_traces is None:
            self.agent_traces = []
    
    def add_input(self, text: str):
        """添加用户输入"""
        self.patient_input.append(text)
        self.updated_at = time.time()
    
    def add_symptom(self, symptom: str):
        """添加症状"""
        if symptom not in self.symptoms:
            self.symptoms.append(symptom)
        self.updated_at = time.time()
    
    def add_agent_trace(self, agent_name: str, summary: str, output: Dict[str, Any]):
        """添加 Agent 执行轨迹"""
        self.agent_traces.append({
            'agent': agent_name,
            'summary': summary,
            'output': output,
            'timestamp': time.time()
        })
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """从字典恢复"""
        data['status'] = SessionStatus(data['status'])
        return cls(**data)


class SessionManager:
    """会话管理器 - 管理多轮对话状态"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._timeout = 3600  # 1小时超时
    
    def create_session(self, session_id: str) -> SessionState:
        """创建新会话"""
        session = SessionState(
            session_id=session_id,
            status=SessionStatus.INIT,
            created_at=time.time(),
            updated_at=time.time()
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话"""
        session = self._sessions.get(session_id)
        if session and time.time() - session.updated_at > self._timeout:
            # 超时会话自动删除
            del self._sessions[session_id]
            return None
        return session
    
    def get_or_create(self, session_id: str) -> SessionState:
        """获取或创建会话"""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session
    
    def update_session(self, session_id: str, **kwargs) -> SessionState:
        """更新会话"""
        session = self.get_or_create(session_id)
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        session.updated_at = time.time()
        return session
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def cleanup_expired(self):
        """清理过期会话"""
        now = time.time()
        expired = [
            sid for sid, sess in self._sessions.items()
            if now - sess.updated_at > self._timeout
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)
    
    def has_scale_scores(self, session: SessionState) -> bool:
        """检查是否已有量表分数"""
        scales = session.scales
        phq9 = scales.get('PHQ9', {}).get('score', 0) if isinstance(scales.get('PHQ9'), dict) else scales.get('PHQ9', 0)
        gad7 = scales.get('GAD7', {}).get('score', 0) if isinstance(scales.get('GAD7'), dict) else scales.get('GAD7', 0)
        return (phq9 and phq9 > 0) or (gad7 and gad7 > 0)
    
    def determine_mode(self, session: SessionState) -> str:
        """判断诊断模式
        
        Returns:
            "quick": 已有量表分数，快速诊断模式
            "guided": 需要引导评估模式
        """
        if self.has_scale_scores(session):
            return "quick"
        return "guided"


# 全局单例
_session_manager = None


def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
