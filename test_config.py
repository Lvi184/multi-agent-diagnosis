#!/usr/bin/env python3
"""
配置验证与系统测试脚本
验证 DeepSeek 配置和多 Agent 系统运行状态
"""
import json
from app.core.config import settings
from app.services.llm_client import DeepSeekClient
from app.schemas.diagnosis import DiagnosisRequest
from app.core.orchestrator import DiagnosisOrchestrator


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("📋 配置检查")
    print("=" * 60)
    print(f"应用名称: {settings.app_name} v{settings.app_version}")
    print(f"LLM 提供商: {settings.llm_provider}")
    print(f"LLM 启用: {settings.enable_llm}")
    print(f"DeepSeek 模型: {settings.deepseek_model}")
    print(f"DeepSeek API Key: {'已配置' if settings.deepseek_api_key else '未配置'}")
    print(f"DeepSeek Base URL: {settings.deepseek_base_url}")
    print(f"使用真实 LangGraph: {settings.use_real_langgraph}")
    print()
    return bool(settings.deepseek_api_key)


def test_deepseek_connection():
    """测试 DeepSeek 连接"""
    print("=" * 60)
    print("🔗 DeepSeek 连接测试")
    print("=" * 60)

    if not settings.deepseek_api_key:
        print("⚠️  未配置 DEEPSEEK_API_KEY，将使用规则回退模式")
        print("💡 提示：请在 .env 文件中填写你的 DeepSeek API Key")
        print("   获取地址：https://platform.deepseek.com/")
        return False

    client = DeepSeekClient()

    if not client.available:
        print("❌ DeepSeek 客户端不可用")
        return False

    try:
        print("正在测试 DeepSeek API 连接...")
        response = client.chat([
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请只回复一句话：连接成功。"}
        ])
        print(f"✅ DeepSeek API 连接成功！")
        print(f"   响应: {response}")
        return True
    except Exception as e:
        print(f"❌ DeepSeek API 连接失败: {e}")
        return False


def test_agent_system():
    """测试多 Agent 系统"""
    print()
    print("=" * 60)
    print("🤖 多 Agent 系统测试")
    print("=" * 60)

    try:
        request = DiagnosisRequest(
            session_id="test-session-001",
            text="我最近两个月情绪低落、失眠、没兴趣，也经常焦虑担心，偶尔觉得活着没有意义。",
            age=22,
            gender="female",
            scale_answers={"PHQ9": 16, "GAD7": 11},
            history=["无明确精神科就诊史"],
        )

        print("正在运行多 Agent 诊断流程...")
        print(f"患者主诉: {request.text}")
        print(f"年龄: {request.age}, 性别: {request.gender}")
        print(f"量表: PHQ-9={request.scale_answers.get('PHQ9')}, "
              f"GAD-7={request.scale_answers.get('GAD7')}")
        print()

        response = DiagnosisOrchestrator().run(request)

        print("✅ 多 Agent 系统运行成功！")
        print()
        print("=" * 60)
        print("📊 诊断结果摘要")
        print("=" * 60)
        result = response.model_dump()

        if result.get('report'):
            report = result['report']
            if report.get('suspected_diagnosis'):
                print(f"疑似诊断: {report['suspected_diagnosis']}")
            if report.get('risk_level'):
                print(f"风险等级: {report['risk_level']}")
            if report.get('recommendations'):
                print(f"建议: {report['recommendations']}")

        print()
        print("=" * 60)
        print("📝 Agent 执行轨迹")
        print("=" * 60)
        for trace in result.get('agent_traces', []):
            agent_name = trace.get('agent', 'Unknown')
            summary = trace.get('summary', '')
            print(f"✅ {agent_name}: {summary}")

        return True

    except Exception as e:
        print(f"❌ 多 Agent 系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print()
    print("🎯 MoodAngels-LangGraph-DeepSeek 系统测试")
    print()

    has_api_key = test_config()
    api_ok = test_deepseek_connection()

    agent_ok = test_agent_system()

    print()
    print("=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    print(f"配置加载: {'✅ 成功' if has_api_key else '⚠️  无API Key(规则模式)'}")
    print(f"DeepSeek API: {'✅ 正常' if api_ok else '⚠️  未连接(规则模式)'}")
    print(f"多 Agent 系统: {'✅ 正常' if agent_ok else '❌ 失败'}")
    print()

    if not has_api_key:
        print("💡 下一步:")
        print("   1. 在 .env 文件中填写 DEEPSEEK_API_KEY")
        print("   2. 获取地址: https://platform.deepseek.com/")
    else:
        print("🎉 系统配置完成！可以开始使用了。")
    print()


if __name__ == "__main__":
    main()
