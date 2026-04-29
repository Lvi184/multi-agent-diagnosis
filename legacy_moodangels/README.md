# legacy_moodangels 融合说明

本目录不再要求保留原 MoodAngels 的代码格式。原因是公开仓库中的代码依赖未公开的数据文件、embedding、病例库、DeepSeek/GPT封装和若干工具函数，直接复制会导致工程不可运行。

本项目已经把公开代码中可复用的思想融合进 `app/agents/moodangels_diagnosis_agent.py`：

- `agent.py` 的 `agent_execute(query, max_request_time=10)` 思想：LLM 决策 + 工具调用 + scratchpad + 最终 finish；
- `tools.py` 的工具思想：病历获取、量表表现、DSM-5相似症状检索、相似病例展示/分析；
- `debate_agents.py` 的思想：正反辩论 + Judge 裁决；
- 三种模式思想：`raw_agent`、`similar_cases_display`、`similar_cases_analyze`。

在当前工程中，这些内容被重构为可运行、可扩展、可接 DeepSeek API 的 LangGraph 节点，而不是直接依赖原始私有数据。
