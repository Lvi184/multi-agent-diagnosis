#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话接口 - 引导式多轮对话
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services import dialogue_service
from app.core.deps import get_optional_user
from app.models import User

router = APIRouter()


class DialogueMessage(BaseModel):
    """对话消息"""
    session_id: str = Field(..., description="会话ID，每次对话保持一致")
    message: str = Field(..., description="用户消息")
    age: Optional[int] = Field(None, description="年龄（可选，首轮建议填写）")
    gender: Optional[str] = Field(None, description="性别（可选，首轮建议填写）")


class DialogueResponse(BaseModel):
    """对话响应"""
    session_id: str
    status: str  # collecting | diagnosing | completed
    reply: str
    collected_info: Optional[Dict[str, Any]] = None
    diagnosis_result: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None


@router.post("", response_model=DialogueResponse, summary="发送对话消息")
async def send_message(
    request: DialogueMessage,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    发送对话消息，支持引导式多轮对话
    
    对话流程：
    1. 用户描述情况 → 系统引导深入询问
    2. 心情 → 睡眠 → 精力 → 负性事件 → 病史 → 风险筛查 → 量表
    3. 信息收集完整后自动进入诊断
    4. 诊断完成后返回完整报告
    
    请求示例：
    {
        "session_id": "demo-session-001",
        "message": "最近心情不好，总是睡不着",
        "age": 25,
        "gender": "female"
    }
    """
    user_id = user.id if user else None
    
    result, reply = await dialogue_service.process_message(
        session_id=request.session_id,
        message=request.message,
        user_id=user_id,
        age=request.age,
        gender=request.gender,
    )
    
    return {
        "session_id": request.session_id,
        "status": result.get("status", "collecting"),
        "reply": reply,
        "collected_info": result.get("collected_info"),
        "diagnosis_result": result.get("diagnosis_result"),
        "intent": result.get("intent"),
        "confidence": result.get("confidence"),
    }


@router.get("/session/{session_id}", summary="获取会话状态")
async def get_session_status(
    session_id: str,
    user: Optional[User] = Depends(get_optional_user),
):
    """获取会话的历史记录和当前状态"""
    history = await dialogue_service.get_session_history(session_id)
    if not history:
        return {"exists": False, "message": "会话不存在"}
    
    return {
        "exists": True,
        **history,
    }


@router.get("/my/sessions", summary="获取我的会话列表（登录用户）")
async def get_my_sessions(user: User = Depends(get_optional_user)):
    """获取当前用户的所有历史会话"""
    if not user:
        return {"logged_in": False, "sessions": []}
    
    sessions = await dialogue_service.get_user_sessions(user.id)
    return {
        "logged_in": True,
        "sessions": sessions,
    }
