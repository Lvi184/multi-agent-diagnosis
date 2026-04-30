#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 依赖注入
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services import auth_service
from app.repositories import user_repo

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    获取当前登录用户
    
    用法：
        @app.get("/protected")
        async def protected(user: User = Depends(get_current_user)):
            return {"user": user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 验证 Token
    user_id = auth_service.verify_token(credentials.credentials)
    if not user_id:
        raise credentials_exception
    
    # 获取用户信息
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """获取当前激活用户（和 get_current_user 一样，保持接口兼容）"""
    return current_user


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    获取用户（可选，未登录返回 None）
    
    用法：
        @app.get("/public")
        async def public(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"logged_in": True, "user": user.username}
            return {"logged_in": False}
    """
    if not credentials:
        return None
    
    try:
        user_id = auth_service.verify_token(credentials.credentials)
        if not user_id:
            return None
        
        user = await user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None
