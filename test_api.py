#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 FastAPI 服务
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 50)
print("测试 FastAPI 服务")
print("=" * 50)

print("\n1. 测试导入...")
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    print("   FastAPI 导入成功")
except Exception as e:
    print(f"   FastAPI 导入失败: {e}")
    print("   请运行: pip install fastapi uvicorn")
    sys.exit(1)

print("\n2. 测试应用导入...")
try:
    from app.main import app
    print("   应用导入成功")
except Exception as e:
    print(f"   应用导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. 创建测试客户端...")
client = TestClient(app)
print("   测试客户端创建成功")

print("\n4. 测试健康检查接口...")
try:
    response = client.get("/")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   主页接口正常")
    else:
        print("   主页接口异常")
except Exception as e:
    print(f"   测试失败: {e}")

print("\n5. 测试诊断接口...")
try:
    request_data = {
        "session_id": "api-test-001",
        "text": "最近情绪不好，失眠，没兴趣",
        "age": 25,
        "gender": "male",
        "scale_answers": {"PHQ9": 12, "GAD7": 8}
    }
    response = client.post("/api/diagnose", json=request_data)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("   诊断接口正常")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Agent 数量: {len(result.get('agent_traces', []))}")
    else:
        print(f"   诊断接口异常: {response.text}")
except Exception as e:
    print(f"   测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("API 测试完成！")
print("=" * 50)
print("\n提示: 启动完整服务请运行:")
print("  uvicorn app.main:app --reload --port 8000")
print("  然后访问: http://127.0.0.1:8000/")
print()
