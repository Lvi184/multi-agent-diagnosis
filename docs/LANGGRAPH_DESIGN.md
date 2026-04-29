# LangGraph 多 Agent 实现设计

本项目将精神疾病辅助诊断流程改造成 LangGraph `StateGraph`。每个 Agent 是一个图节点，所有节点通过统一的 `DiagnosisState` 读写共享状态。

## 节点顺序

```text
START
  -> Intake Agent
  -> Structuring Agent
  -> Scale Assessment Agent
  -> MoodAngels Diagnosis Agents
  -> Model Verification Agent
  -> Knowledge Agent
  -> Differential Diagnosis Agent
  -> Risk Assessment Agent
  -> Validator Agent
  -> Report Agent
  -> END
```

## 状态对象

核心状态位于 `app/graph/state.py`：

- `text/history/scale_answers`：输入信息
- `intake`：病史采集结果
- `structured`：结构化病历
- `scales`：量表评分
- `diagnosis`：MoodAngels 核心诊断结果
- `model_verification`：MentalBERT / NeuroCheck 外部验证结果
- `knowledge`：DSM-5 / ICD RAG、知识图谱、规则库证据
- `differential`：鉴别诊断
- `risk`：风险评估
- `validation`：安全校验
- `report`：最终报告
- `agent_traces`：全过程可解释轨迹

## 为什么用 LangGraph

LangGraph 官方图 API 支持以共享状态构建有状态工作流，节点读取状态并返回局部更新，适合多步骤、多 Agent、可观测的诊断辅助流程。

## 原 MoodAngels 的接入方式

`app/agents/moodangels_diagnosis_agent.py` 保留 `LegacyMoodAngelsAdapter`。如果把原始 MoodAngels 仓库的 `code/` 文件复制到：

```text
legacy_moodangels/code/
```

并在 `.env` 中设置：

```text
USE_LEGACY_MOODANGELS=true
LEGACY_MOODANGELS_PATH=legacy_moodangels/code
```

系统会优先调用原始 `agent_execute`；否则自动使用兼容版启发式 MoodAngels 流程，保证系统可运行。
