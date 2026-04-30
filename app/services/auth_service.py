#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务 - JWT 登录注册
"""
from typing import Optional, Tuple
import time
from app.core.config import settings
from app.core.jwt_utils import create_jwt, decode_jwt


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    @property
    def user_repo(self):
        """延迟导入，避免循环引用"""
        from app.repositories import user_repo
        return user_repo
    
    async def register(self, username: str, password: str, email: str = None, **kwargs) -> Tuple[bool, str, Optional[dict]]:
        """
        用户注册
        
        Returns:
            (是否成功, 消息, 用户对象)
        """
        # 检查用户名是否存在
        existing = await self.user_repo.get_by_username(username)
        if existing:
            return False, "用户名已存在", None
        
        # 密码强度校验
        if len(password) < 8:
            return False, "密码至少需要8位", None
        
        # 创建用户
        try:
            user = await self.user_repo.create_user(username, password, email, **kwargs)
            return True, "注册成功", user
        except Exception as e:
            return False, f"注册失败: {str(e)}", None
    
    async def login(self, username: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """
        用户登录
        
        Returns:
            (是否成功, 消息, {access_token, refresh_token, user})
        """
        user = await self.user_repo.get_by_username(username)
        if not user:
            return False, "用户名或密码错误", None
        
        if not user.is_active:
            return False, "账户已被禁用", None
        
        if not self.user_repo.verify_password(password, user.password_hash):
            return False, "用户名或密码错误", None
        
        # 生成 Token
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        
        return True, "登录成功", {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname or user.username,
                "email": user.email,
                "role": user.role,
            }
        }
    
    def verify_token(self, token: str) -> Optional[int]:
        """
        验证 Token，返回用户 ID
        
        Returns:
            user_id 或 None（Token 无效/过期）
        """
        payload = decode_jwt(token, self.secret_key)
        if payload:
            return payload.get("sub")
        return None
    
    async def refresh_token(self, refresh_token: str) -> Tuple[bool, str, Optional[dict]]:
        """
        刷新令牌
        
        Returns:
            (是否成功, 消息, {access_token})
        """
        user_id = self.verify_token(refresh_token)
        if not user_id:
            return False, "刷新令牌无效或已过期", None
        
        # 验证用户是否存在
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return False, "用户不存在或已被禁用", None
        
        # 生成新的访问令牌
        new_access_token = self._create_access_token(user_id)
        
        return True, "刷新成功", {
            "access_token": new_access_token,
            "token_type": "bearer",
        }
    
    def _create_access_token(self, user_id: int) -> str:
        """创建访问令牌（默认4小时）"""
        expire = int(time.time()) + self.access_token_expire * 60
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return create_jwt(to_encode, self.secret_key)
    
    def _create_refresh_token(self, user_id: int) -> str:
        """创建刷新令牌（默认7天）"""
        expire = int(time.time()) + self.refresh_token_expire * 24 * 60 * 60
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return create_jwt(to_encode, self.secret_key)


# 全局单例
auth_service = AuthService()
