# LangGraph + DeepSeek 融合设计

## 1. 为什么不直接复制 legacy_moodangels

MoodAngels 公开代码依赖未公开数据、embedding、病例库、LLM封装和本地路径。直接复制会导致无法运行。因此本项目采用“思想融合而非格式复制”的策略：保留公开代码中的 Agent/Tool/Debate 架构，把它重构为 LangGraph 节点。

## 2. DeepSeek 接入

`app/services/llm_client.py` 使用 DeepSeek 的 OpenAI-compatible Chat Completions 接口：

```text
POST {DEEPSEEK_BASE_URL}/v1/chat/completions
Authorization: Bearer {DEEPSEEK_API_KEY}
model: {DEEPSEEK_MODEL}
```

每个需要推理的 Agent 都继承 `BaseAgent`，通过 `self.llm.json_chat()` 调用 DeepSeek。若未配置 API Key，则返回规则兜底结果。

## 3. 前端对话窗口

`frontend/index.html` 是单文件聊天窗口，后端通过 FastAPI 静态资源挂载到 `/`。用户输入会调用 `/api/chat`，后端再执行完整 LangGraph 流程。

## 4. 论文表述建议

本文将 MoodAngels 原有的工具调用式多智能体诊断流程重构为基于 LangGraph 的有状态工作流。系统通过统一 `DiagnosisState` 在 Intake、Structuring、Scale、MoodAngels Diagnosis、Model Verification、Knowledge、Differential Diagnosis、Risk Assessment、Validator 与 Report Agent 之间传递中间结果，并通过 DeepSeek 大模型完成可替换的语言理解与推理增强。
