# MoodAngels v2.0 升级指南

## 🎯 概述

v1.0 → v2.0 从「演示原型」升级为「企业级产品」

## ✨ 升级亮点

| 维度 | v1.0（演示版）| v2.0（企业级）|
|-----|--------------|----------------|
| 架构 | 单层，逻辑混杂 | 三层架构：API → Service → Repository |
| 用户系统 | 只有 session_id | 完整的用户注册/登录/JWT认证 |
| 数据持久化 | 内存字典，重启丢失 | SQLite/PostgreSQL 持久化存储 |
| 历史记录 | 不保存 | 所有会话+诊断 完整历史记录 |
| 安全 | 无认证、无限流 | 登录限流 + 密码加密 + JWT令牌 |
| 日志 | print打印 | Loguru 结构化日志 + 诊断专用日志 |
| 配置管理 | 硬编码 | .env 环境变量 |
| 监控接口 | 无 | 健康检查 + 版本接口 + 用户统计 |

## 🚀 快速开始

### 1. 安装依赖

```bash
# 升级包
pip install -r requirements_v2.txt

# 或者用 UV（推荐）
# pip install uv
# uv pip install -r requirements_v2.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，修改以下内容
vim .env
```

**必须修改的配置：
```env
SECRET_KEY=你的32位以上随机密钥
SWAGGER_UI_PASSWORD=设置一个强密码
```

### 3. 启动服务

```bash
# 方式一：开发模式（自动重载）
python -m uvicorn app.main_v2:app --port 8000 --reload

# 方式二：生产模式
uvicorn app.main_v2:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 验证安装

打开浏览器访问：
- 主页：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

## 📂 新的目录结构

```
moodangels_langgraph_deepseek/
├── app/
│   ├── api/v1/              # ✨ 新增：API 层
│   │   ├── base.py         # 健康检查、版本信息
│   │   ├── auth.py         # 注册登录
│   │   ├── dialogue.py     # 对话接口
│   │   └── diagnosis.py    # 诊断记录
│   │
│   ├── services/            # ✨ 新增：业务逻辑层
│   │   ├── base_service.py  # 基础 Service
│   │   ├── auth_service.py  # 认证服务
│   │   └── dialogue_service.py  # 对话+诊断服务
│   │
│   ├── repositories/        # ✨ 新增：数据访问层
│   │   ├── base_repo.py     # 通用 CRUD
│   │   ├── user_repo.py    # 用户数据访问
│   │   └── diagnosis_repo.py # 诊断数据访问
│   │
│   ├── models/           # ✨ 新增：数据模型层
│   │   ├── base.py         # 基础模型
│   │   ├── user.py         # 用户模型
│   │   └── diagnosis.py    # 诊断模型
│   │
│   ├── core/              # ✨ 重构：核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库配置
│   │   ├── logging_config.py # 日志配置
│   │   └── deps.py         # 依赖注入
│   │
│   └── main_v2.py       # ✨ 新增：v2 启动入口
│
├── logs/                # ✨ 新增：日志目录
│   ├── app_2026-04-30.log
│   ├── error_2026-04-30.log
│   └── diagnosis_2026-04-30.log
│
├── uploads/             # ✨ 新增：文件上传目录
│
├── data/               # ✨ 新增：数据目录
│   └── db.sqlite3   # SQLite 数据库
│
├── .env.example       # ✨ 新增：环境变量模板
├── requirements_v2.txt  # ✨ 新增：v2 依赖列表
└── V2_UPGRADE_GUIDE.md  # 本文档
```

## 🔌 API 接口总览

### 基础接口 `GET /api/v1/*`
- `GET /health` - 健康检查
- `GET /version` - 版本信息

### 认证接口 `POST /api/v1/auth/*`
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `POST /refresh` - 刷新令牌
- `GET /me` - 获取当前用户信息

### 对话接口 `POST /api/v1/dialogue/*`
- `POST /` - 发送对话消息
- `GET /session/{session_id}` - 获取会话状态
- `GET /my/sessions` - 获取我的会话列表

### 诊断接口 `GET /api/v1/diagnosis/*`
- `GET /records` - 获取我的诊断记录（需登录）
- `GET /records/{id}` - 获取诊断详情
- `POST /records/{id}/feedback` - 提交反馈

## 🔄 数据迁移（v1 → v2

### 暂时兼容方案

v2 默认兼容 v1 的前端：
- ✅ 旧的 `/api/chat` 接口仍可使用（在 `app/api/routes.py`）
- ✅ 所有 Agent 逻辑不变
- ✅ 意图分类器不变
- ✅ 引导式对话逻辑不变

### 建议迁移步骤

1. **先跑通 v2 版本
2. **把 `app/graph/workflow.py` 接入 `dialogue_service.py` 中的 `_run_diagnosis` 方法
3. **调试通过后，切换前端调用 v2 接口
4. **逐步迁移旧数据

## 🛡 安全最佳实践

1. **生产环境必须配置：
   - ✅ 设置强密码
   - ✅ `DEBUG=false
   - ✅ 启用 HTTPS
   - ✅ 修改所有 `SECRET_KEY` 为随机字符串
   - ✅ 配置正确的 CORS_ORIGINS
   - ✅ 使用 PostgreSQL 替换 SQLite

2. **密码强度校验：
   - 最小 8 位
   - 内置 bcrypt 加密

3. **登录限流：
   - 每分钟 5 次，防暴力破解

## 📊 日志说明

三类日志：

1. **app_YYYY-MM-DD.log** - 普通应用日志
2. **error_YYYY-MM-DD.log** - 错误日志（单独保存）
3. **diagnosis_YYYY-MM-DD.log** - 诊断专用日志

自动管理：
- 按天滚动
- 保留 30-90 天
- 自动压缩旧日志
- 结构化输出

## 🚧 后续迭代计划

### v2.1（近期）
- [ ] 完整接入多 Agent 诊断流程
- [ ] 对话引导的量表答题
- [ ] 管理后台 API
- [ ] 消息通知（邮件/短信）

### v2.2（中期）
- [ ] 管理员看板 + 统计分析
- [ ] WebSocket 实时对话
- [ ] 导出 PDF 报告
- [ ] 文件上传（病历）

---

## 💡 常见问题

### Q: 原来的 v1 还能用吗？

A: 可以！v1 和 v2 完全兼容。v1 入口：`uvicorn app.main:app --port 8000`

### Q: 数据库会自动创建表吗？

A: 开发模式（DEBUG=true）启动时会自动创建表。生产环境建议用 aerich 做迁移：
```bash
aerich init-db  # 初始化
aerich migrate   # 生成迁移文件
aerich upgrade  # 执行迁移
```

### Q: 如何创建管理员用户？

A: 注册后，手动修改数据库 `users` 表的 `role` 字段为 `admin`

---

祝使用愉快！🎉
