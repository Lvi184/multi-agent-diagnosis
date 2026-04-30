#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证接口 - 注册/登录/刷新令牌
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services import auth_service
from app.core.config import settings
from app.core.deps import get_current_user
from app.models import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    
    @validator('password')
    def password_complexity(cls, v):
        """密码复杂度校验"""
        if len(v) < 8:
            raise ValueError("密码至少需要8位")
        return v


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse, summary="用户登录")
# @limiter.limit(settings.LOGIN_RATE_LIMIT)  # 登录限流，每分钟 5 次
async def login(request: LoginRequest):
    """
    用户登录
    
    请求示例：
    {
        "username": "demo",
        "password": "password123"
    }
    """
    success, message, result = await auth_service.login(request.username, request.password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    return result


@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(request: RegisterRequest):
    """
    用户注册
    
    请求示例：
    {
        "username": "demo",
        "password": "password123",
        "email": "demo@example.com",
        "nickname": "演示用户"
    }
    """
    success, message, user = await auth_service.register(
        username=request.username,
        password=request.password,
        email=request.email,
        nickname=request.nickname,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    
    # 注册成功后自动登录
    _, _, token_result = await auth_service.login(request.username, request.password)
    return token_result


@router.post("/refresh", summary="刷新访问令牌")
async def refresh_token(refresh_token: str):
    """
    刷新访问令牌（当 access_token 过期后使用）
    
    请求示例：refresh_token=你的刷新令牌
    """
    success, message, result = await auth_service.refresh_token(refresh_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    return result


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname or user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
    }
