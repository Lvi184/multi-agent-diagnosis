# 融合说明

MoodAngels 原 `agent.py` 的核心入口是 `agent_execute(query, max_request_time=10)`，其工作方式是：构造 prompt，调用 LLM，解析 JSON action，再通过 `tools_map` / `tools_map_syn` 调用工具，直到 action 为 `finish`。本项目把这个入口封装为 `LegacyMoodAngelsAdapter`，同时提供内置的 MoodAngels-compatible 引擎，以便没有原数据集和 API Key 时仍可运行。
