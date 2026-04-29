# MoodAngels 公开代码摘要

公开仓库 `code/` 目录包含：

- `agent.py`：核心入口 `agent_execute(query, max_request_time=10)`，通过 prompt 调用 LLM，解析 JSON action，根据 action 调用工具，直到 `finish`。
- `tools.py`：包含 `get_scale_performances`、`retrieve_similar_symptoms`、`previous_cases_display`、`previous_scales_display`、`previous_cases_analysis`、`previous_scales_analysis` 等工具，并定义 `tools_map` / `tools_map_syn`。
- `debate_agents.py`：引入 tools 和 debate prompt，用于辩论式诊断流程。
- `prompt.py` / `debate_prompt.py`：负责构造 Agent 和 Debate 相关提示词。

本项目的融合方式：

1. 原 `agent_execute` → LangGraph 中的 `MoodAngelsDiagnosisAgent.run()`。
2. 原 `tools_map` → 当前系统内置的结构化病历、量表、知识、风险等 Agent 节点。
3. 原相似病例检索 → `Angel.D` 的 `similar_case_signal`，后续可替换为真实向量库/病例库。
4. 原案例差异分析 → `Angel.C` 的 similarities / differences。
5. 原 Debate + Judge → `debate` 与 `judge` 字段。
6. 原 DeepSeek 调用 → `app/services/llm_client.py` 统一 DeepSeek API 客户端。
