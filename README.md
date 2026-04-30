# Multi-Agent Diagnosis 多Agent精神疾病辅助筛查系统

基于多Agent辩论框架的端到端精神疾病辅助诊断系统，完整集成 DeepSeek 大模型，支持 LangGraph 工作流编排。

> ⚠️ **重要声明**：本项目仅用于科研、教学、课程设计、论文原型和辅助筛查演示，不构成医学确诊、治疗建议或替代医生判断。

## ✨ 核心特性

- **10 个专业 Agent 协同**：从病史采集到报告生成的完整流程
- **DeepSeek 大模型集成**：开箱即用，支持所有 DeepSeek 模型
- **双模式运行**：真实 LLM 推理 / 规则回退演示（无需 API Key）
- **LangGraph 工作流编排**：可配置、可扩展、可追踪
- **FastAPI 后端 + Web 前端**：完整的前后端方案
- **安全校验机制**：医疗合规、禁止确诊、高危拦截

## 🏗️ Agent 流程

```text
患者输入
  ↓
Intake Agent：对话入口与病史采集（主诉、现病史、用药史、自杀初筛）
  ↓
Structuring Agent：数据标准化（结构化病历、症状抽取、时间线）
  ↓
Scale Assessment Agent：量表评估（PHQ-9 / GAD-7 / HAMD / HAMA 题目级分析）
  ↓
MoodAngels Diagnosis Agents：核心诊断（Angel.R / Angel.D / Angel.C / Debate / Judge）
  ↓
Model Verification Agent：外部模型验证（MentalBERT / NeuroCheck 兼容）
  ↓
Knowledge Agent：知识增强（DSM-5 RAG / 知识图谱 / 规则库）
  ↓
Differential Diagnosis Agent：鉴别诊断（抑郁/双相/焦虑/精神分裂）
  ↓
Risk Assessment Agent：风险评估（自杀/自伤/躁狂/精神病性症状）
  ↓
Validator Agent：安全校验（禁止确诊、高危拦截、合规检查）
  ↓
Report Agent：结果生成（疑似诊断、证据链、就医建议）
```

## 🚀 快速开始

### 前置要求

- Python 3.8+
- DeepSeek API Key（可选，不填也可演示）

### 1. 安装依赖

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置 DeepSeek（可选）

编辑 `.env` 文件（已自动创建），填入你的 API Key：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 不填 API Key 也能完整运行！系统会自动切换到规则回退演示模式。

详细配置指南请查看：[DEEPSEEK配置指南.md](DEEPSEEK配置指南.md)

### 3. 运行测试

```bash
# 测试 Agent 导入与基础功能
python test_agents_simple.py

# 测试完整诊断工作流
python test_full_workflow.py

# 运行命令行 Demo
python run_demo.py
```

### 4. 启动 Web 服务

```bash
uvicorn app.main:app --reload --port 8000
```

打开浏览器访问：**http://127.0.0.1:8000/**

## 📡 API 接口

### POST `/api/diagnose` - 完整诊断

请求体：
```json
{
  "session_id": "demo-001",
  "text": "最近2个月情绪低落，睡不着，对事情没兴趣，有时觉得不想活。",
  "age": 22,
  "gender": "female",
  "scale_answers": {"PHQ9": 18, "GAD7": 11}
}
```

### POST `/api/chat` - 对话式筛查

请求体：
```json
{
  "session_id": "web-demo",
  "message": "最近情绪不好，总是失眠",
  "age": 22,
  "gender": "female",
  "scale_answers": {"PHQ9": 0, "GAD7": 0},
  "history": []
}
```

## 📁 项目结构

```
MoodAngels-LangGraph-DeepSeek/
├── app/
│   ├── agents/                      # 10 个专业 Agent
│   │   ├── intake_agent.py         # 病史采集
│   │   ├── structuring_agent.py    # 数据结构化
│   │   ├── scale_agent.py          # 量表评估
│   │   ├── moodangels_diagnosis_agent.py  # MoodAngels 核心
│   │   ├── model_verification_agent.py    # 外部模型验证
│   │   ├── knowledge_agent.py      # 知识增强
│   │   ├── differential_agent.py   # 鉴别诊断
│   │   ├── risk_agent.py           # 风险评估
│   │   ├── validator_agent.py      # 安全校验
│   │   └── report_agent.py         # 报告生成
│   ├── graph/
│   │   ├── workflow.py             # LangGraph 工作流
│   │   └── state.py                # 共享状态定义
│   ├── services/
│   │   ├── llm_client.py           # DeepSeek API 客户端
│   │   └── rules.py                # 规则引擎
│   ├── core/
│   │   ├── config.py               # 配置管理
│   │   └── orchestrator.py         # 编排器
│   ├── schemas/
│   │   └── diagnosis.py            # Pydantic 模型
│   ├── api/
│   │   └── routes.py               # FastAPI 路由
│   └── main.py                     # 应用入口
├── frontend/
│   └── index.html                  # Web 对话界面
├── data/
│   ├── knowledge/                  # DSM-5/ICD 知识库
│   ├── rules/                      # 风险规则
│   └── samples/                    # 示例数据
├── legacy_moodangels/              # 原 MoodAngels 代码摘要
├── docs/                           # 设计文档
├── .env                            # 环境配置（已创建）
├── .env.example                    # 配置模板
├── requirements.txt                # Python 依赖
├── run_demo.py                     # 命令行 Demo
├── test_agents_simple.py           # Agent 测试
├── test_full_workflow.py           # 完整工作流测试
├── test_import.py                  # 导入测试
├── DEEPSEEK配置指南.md             # DeepSeek 详细配置
└── README.md                       # 本文件
```

## 🎯 测试结果

✅ 项目已通过完整测试：

- **所有 Agent 正常运行**：10 个 Agent 全部测试通过
- **完整工作流正常**：从输入到报告生成完整链路
- **DeepSeek 兼容**：API 客户端已集成，可随时启用真实 LLM
- **Web 服务正常**：FastAPI + 前端完整可用

## 📚 文档资源

- [DEEPSEEK配置指南.md](DEEPSEEK配置指南.md) - DeepSeek API 配置完整指南
- `docs/` 目录 - 系统设计文档、架构图、集成指南

## 🔧 高级配置

### 切换 DeepSeek 模型

编辑 `.env`：
```env
DEEPSEEK_MODEL=deepseek-chat      # 标准对话（默认）
# DEEPSEEK_MODEL=deepseek-coder   # 代码模型
# DEEPSEEK_MODEL=deepseek-reasoner  # 推理模型
```

### 启用真实 LangGraph

需要先安装依赖：
```bash
pip install langgraph langchain-core
```

然后编辑 `.env`：
```env
USE_REAL_LANGGRAPH=true
```

## ⚠️ 使用须知

1. **非医疗设备**：本系统仅用于辅助筛查和科研演示
2. **禁止确诊**：系统不会输出确诊结论，仅提供疑似诊断建议
3. **高危拦截**：检测到自杀/自伤等高风险时会强制输出紧急就医建议
4. **隐私保护**：请确保使用符合医疗数据隐私法规的环境

## 🤝 致谢

本项目基于以下开源思想：

- **MoodAngels**：多智能体辩论诊断框架
- **LangGraph**：多 Agent 工作流编排
- **DeepSeek**：大语言模型 API

## 📄 许可证

本项目仅用于学术研究和教育目的。
