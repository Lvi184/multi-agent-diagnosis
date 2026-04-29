from __future__ import annotations
from typing import Any, Callable, Dict, List, Tuple
from app.agents.intake_agent import IntakeAgent
from app.agents.structuring_agent import StructuringAgent
from app.agents.scale_agent import ScaleAssessmentAgent
from app.agents.moodangels_diagnosis_agent import MoodAngelsDiagnosisAgent
from app.agents.model_verification_agent import ModelVerificationAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.differential_agent import DifferentialDiagnosisAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.validator_agent import ValidatorAgent
from app.agents.report_agent import ReportAgent
from app.core.config import settings
from app.graph.state import DiagnosisState
from app.schemas.diagnosis import DiagnosisRequest


def _trace(agent_name: str, summary: str, output: Dict[str, Any], state: DiagnosisState) -> Dict[str, Any]:
    traces = list(state.get('agent_traces', []))
    traces.append({'agent': agent_name, 'summary': summary, 'output': output})
    return {'agent_traces': traces, 'current_step': agent_name}


class SequentialGraphFallback:
    def __init__(self, nodes: List[Tuple[str, Callable[[DiagnosisState], Dict[str, Any]]]]):
        self.nodes = nodes
    def invoke(self, initial_state: DiagnosisState) -> DiagnosisState:
        state = dict(initial_state)
        for _, node in self.nodes:
            state.update(node(state))
        return state
    def get_graph(self):
        return self
    def draw_mermaid(self):
        order = ['START'] + [name for name, _ in self.nodes] + ['END']
        return 'flowchart TD\n' + '\n'.join(f'  {order[i]} --> {order[i+1]}' for i in range(len(order)-1))


class LangGraphDiagnosisWorkflow:
    def __init__(self) -> None:
        self.intake = IntakeAgent(); self.structuring = StructuringAgent(); self.scale = ScaleAssessmentAgent()
        self.diagnosis = MoodAngelsDiagnosisAgent(); self.model_verification = ModelVerificationAgent()
        self.knowledge = KnowledgeAgent(); self.differential = DifferentialDiagnosisAgent(); self.risk = RiskAssessmentAgent()
        self.validator = ValidatorAgent(); self.report = ReportAgent()
        self.nodes = [
            ('intake_agent', self.intake_node), ('structuring_agent', self.structuring_node),
            ('scale_assessment_agent', self.scale_node), ('moodangels_diagnosis_agents', self.diagnosis_node),
            ('model_verification_agent', self.model_verification_node), ('knowledge_agent', self.knowledge_node),
            ('differential_diagnosis_agent', self.differential_node), ('risk_assessment_agent', self.risk_node),
            ('validator_agent', self.validator_node), ('report_agent', self.report_node)]
        self.graph = self._compile()
    def _compile(self):
        if not settings.use_real_langgraph:
            return SequentialGraphFallback(self.nodes)
        from langgraph.graph import END, START, StateGraph
        graph = StateGraph(DiagnosisState)
        for name, fn in self.nodes: graph.add_node(name, fn)
        edges = [('START','intake_agent'), ('intake_agent','structuring_agent'), ('structuring_agent','scale_assessment_agent'),
                 ('scale_assessment_agent','moodangels_diagnosis_agents'), ('moodangels_diagnosis_agents','model_verification_agent'),
                 ('model_verification_agent','knowledge_agent'), ('knowledge_agent','differential_diagnosis_agent'),
                 ('differential_diagnosis_agent','risk_assessment_agent'), ('risk_assessment_agent','validator_agent'),
                 ('validator_agent','report_agent'), ('report_agent','END')]
        for a,b in edges:
            graph.add_edge(START if a=='START' else a, END if b=='END' else b)
        return graph.compile()
    def invoke(self, request: DiagnosisRequest | Dict[str, Any]) -> DiagnosisState:
        if isinstance(request, DiagnosisRequest):
            state = {'session_id': request.session_id, 'text': request.text, 'age': request.age, 'gender': request.gender,
                     'history': request.history, 'scale_answers': request.scale_answers, 'agent_traces': [], 'errors': []}
        else:
            state = {'session_id': request.get('session_id','demo-session'), 'text': request.get('text',''), 'age': request.get('age'),
                     'gender': request.get('gender'), 'history': request.get('history',[]), 'scale_answers': request.get('scale_answers',{}),
                     'agent_traces': [], 'errors': []}
        return self.graph.invoke(state)
    def _request_like(self, state):
        class RequestLike: pass
        req = RequestLike(); req.session_id = state.get('session_id',''); req.text = state.get('text','')
        req.age = state.get('age'); req.gender = state.get('gender'); req.history = state.get('history', [])
        req.scale_answers = state.get('scale_answers', {}); return req
    def intake_node(self, state):
        out = self.intake.run(self._request_like(state)); upd = {'intake': out, 'next_action': 'structuring_agent'}
        upd.update(_trace(self.intake.name, '完成患者输入、多轮问答入口、病史采集和自伤自杀初筛', out, state)); return upd
    def structuring_node(self, state):
        out = self.structuring.run(state['intake']); upd = {'structured': out, 'next_action': 'scale_assessment_agent'}
        upd.update(_trace(self.structuring.name, '完成对话到结构化病历转换，抽取症状、时间线、严重程度和量表整理提示', out, state)); return upd
    def scale_node(self, state):
        out = self.scale.run(state.get('scale_answers', {})); upd = {'scales': out, 'next_action': 'moodangels_diagnosis_agents'}
        upd.update(_trace(self.scale.name, '完成PHQ-9/GAD-7/HAMD/HAMA评分和题目级分析', out, state)); return upd
    def diagnosis_node(self, state):
        out = self.diagnosis.run(state['structured'], state['scales']); upd = {'diagnosis': out, 'next_action': 'model_verification_agent'}
        upd.update(_trace(self.diagnosis.name, '完成融合版MoodAngels：Angel.R、Angel.D、Angel.C、Debate、Judge', out, state)); return upd
    def model_verification_node(self, state):
        out = self.model_verification.run(state.get('text',''), state['diagnosis']); upd = {'model_verification': out, 'next_action': 'knowledge_agent'}
        upd.update(_trace(self.model_verification.name, '完成MentalBERT/NeuroCheck兼容验证和外部风险信号汇总', out, state)); return upd
    def knowledge_node(self, state):
        out = self.knowledge.run(state['structured'], state['diagnosis']); upd = {'knowledge': out, 'next_action': 'differential_diagnosis_agent'}
        upd.update(_trace(self.knowledge.name, '完成DSM-5/ICD RAG、知识图谱和规则库强约束', out, state)); return upd
    def differential_node(self, state):
        out = self.differential.run(state['structured'], state['diagnosis']); upd = {'differential': out, 'next_action': 'risk_assessment_agent'}
        upd.update(_trace(self.differential.name, '完成抑郁/双相/焦虑/精神分裂谱系鉴别诊断', out, state)); return upd
    def risk_node(self, state):
        out = self.risk.run(state.get('text',''), state['structured'], state['model_verification']); upd = {'risk': out, 'next_action': 'validator_agent'}
        upd.update(_trace(self.risk.name, '完成自杀、自伤、躁狂和精神病性症状风险分级', out, state)); return upd
    def validator_node(self, state):
        out = self.validator.run({'diagnosis': state['diagnosis'], 'risk': state['risk']}); upd = {'validation': out, 'next_action': 'report_agent'}
        upd.update(_trace(self.validator.name, '完成禁止确诊、高危风险拦截和医疗合规输出检查', out, state)); return upd
    def report_node(self, state):
        out = self.report.run(state); upd = {'report': out, 'next_action': 'end'}
        upd.update(_trace(self.report.name, '完成疑似诊断、风险等级、证据链和就医建议报告生成', out, state)); return upd


def build_diagnosis_graph(): return LangGraphDiagnosisWorkflow().graph

def run_langgraph_workflow(request: DiagnosisRequest | Dict[str, Any]) -> DiagnosisState: return LangGraphDiagnosisWorkflow().invoke(request)
