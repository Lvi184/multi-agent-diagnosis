from app.schemas.diagnosis import DiagnosisRequest
from app.core.orchestrator import DiagnosisOrchestrator


if __name__ == "__main__":
    request = DiagnosisRequest(
        session_id="demo-langgraph-001",
        text="我最近两个月情绪低落、失眠、没兴趣，也经常焦虑担心，偶尔觉得活着没有意义。",
        age=22,
        gender="female",
        scale_answers={"PHQ9": 16, "GAD7": 11},
        history=["无明确精神科就诊史"],
    )
    response = DiagnosisOrchestrator().run(request)
    print(response.model_dump_json(indent=2, ensure_ascii=False))
