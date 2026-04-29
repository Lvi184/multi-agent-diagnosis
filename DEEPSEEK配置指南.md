# DeepSeek 配置与使用指南

## 📋 目录

1. [获取 DeepSeek API Key](#获取-deepseek-api-key)
2. [配置项目](#配置项目)
3. [验证配置](#验证配置)
4. [常见问题](#常见问题)

---

## 🔑 获取 DeepSeek API Key

### 步骤 1：注册账号

访问 DeepSeek 开放平台：
- 官网：https://platform.deepseek.com/
- 注册并登录你的账号

### 步骤 2：获取 API Key

1. 登录后进入控制台
2. 点击左侧菜单的「API Key」
3. 点击「创建新的 API Key」
4. 复制生成的 Key（格式类似 `sk-xxxxxxxxxxxxxxxxxxxxxxxxxx`）

> **重要提示**：
> - API Key 只会显示一次，请妥善保存
> - 不要将 API Key 提交到公开代码仓库
> - 建议定期轮换 API Key

---

## ⚙️ 配置项目

### 方法 1：编辑 .env 文件（推荐）

项目根目录已创建 `.env` 文件，编辑它：

```env
# DeepSeek 大模型配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx  # 填入你的 API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60
LLM_PROVIDER=deepseek
ENABLE_LLM=true

# 是否使用真实 LangGraph（需要安装 langgraph 依赖）
USE_REAL_LANGGRAPH=false

# 跨域配置
CORS_ALLOW_ORIGINS=*
```

### 方法 2：环境变量（临时）

也可以通过环境变量设置（适用于临时测试）：

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxx"

# Windows CMD
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx

# Linux/Mac
export DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## ✅ 验证配置

### 1. 运行配置测试脚本

```bash
python test_config_simple.py
```

### 2. 运行完整工作流测试

```bash
python test_full_workflow.py
```

### 3. 运行命令行 Demo

```bash
python run_demo.py
```

### 4. 启动 Web 服务

```bash
uvicorn app.main:app --reload --port 8000
```

然后访问：http://127.0.0.1:8000/

---

## 📊 支持的 DeepSeek 模型

| 模型名称 | 说明 | 适用场景 |
|---------|------|---------|
| `deepseek-chat` | 标准对话模型（默认） | 通用诊断对话 |
| `deepseek-coder` | 代码模型 | 代码生成相关 |
| `deepseek-reasoner` | 推理模型 | 需要深度推理的场景 |

在 `.env` 中修改 `DEEPSEEK_MODEL` 即可切换模型。

---

## ❓ 常见问题

### Q1: 不填 API Key 可以运行吗？

**可以**。系统设计了规则回退模式，即使没有 API Key 也能完整运行所有 Agent 流程，方便：
- 本地演示
- 论文答辩展示
- 无网络环境测试

只是诊断逻辑会使用预设规则，而不是真实 LLM 推理。

### Q2: 为什么连接失败？

可能原因：

1. **API Key 错误**：检查是否复制完整，没有多余空格
2. **网络问题**：确保能访问 `api.deepseek.com`
3. **配额不足**：检查 DeepSeek 账户余额
4. **超时**：增加 `.env` 中的 `DEEPSEEK_TIMEOUT` 值

### Q3: 如何查看 API 调用消耗？

登录 DeepSeek 平台控制台：
- 查看「消费记录」
- 查看「余额」
- 设置「用量告警」

### Q4: 可以使用其他兼容 OpenAI 格式的 API 吗？

可以。修改 `.env`：

```env
DEEPSEEK_BASE_URL=https://api.example.com/v1
DEEPSEEK_API_KEY=your-key
```

只要是 OpenAI 兼容的 `/chat/completions` 接口都可以。

### Q5: LangGraph 是什么？需要开启吗？

LangGraph 是 LangChain 推出的多 Agent 编排框架。本项目：

- 默认 `USE_REAL_LANGGRAPH=false`：使用内置顺序执行器，无需额外依赖
- 设置 `USE_REAL_LANGGRAPH=true`：使用真实 LangGraph（需要 `pip install langgraph langchain-core`）

对于大多数演示和测试场景，保持 `false` 即可。

---

## 🔒 安全最佳实践

1. **不要硬编码 API Key**：始终使用环境变量或 `.env` 文件
2. **添加 .env 到 .gitignore**：避免不小心提交到代码仓库
3. **设置最小权限**：API Key 只授予必要的权限
4. **定期轮换 Key**：建议每 3-6 个月更换一次 API Key
5. **设置用量告警**：在 DeepSeek 控制台设置预算告警

---

## 📞 技术支持

如遇到问题：
1. 检查 DeepSeek 平台状态：https://status.deepseek.com/
2. 查看项目文档：`docs/` 目录
3. 查看 DeepSeek 官方文档：https://platform.deepseek.com/docs

---

## 📝 更新日志

- **v2.0.0**：完整 DeepSeek 集成，支持规则回退模式
