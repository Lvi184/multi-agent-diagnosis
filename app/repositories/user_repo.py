#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据访问层
"""
from typing import Optional
import hashlib
import secrets
from app.models import User
from .base_repo import BaseRepository


def hash_password(password: str) -> str:
    """密码哈希：salt + sha256（不需要 bcrypt，避免版本问题）"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256(f"{salt}{password}".encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        salt, _hash = hashed_password.split("$")
        hash_obj = hashlib.sha256(f"{salt}{plain_password}".encode())
        return secrets.compare_digest(hash_obj.hexdigest(), _hash)
    except Exception:
        return False


class UserRepository(BaseRepository):
    """用户 Repository"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.model.filter(username=username, is_deleted=False).first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.model.filter(email=email, is_deleted=False).first()
    
    async def create_user(self, username: str, password: str, email: str = None, **kwargs) -> User:
        """创建用户（密码自动哈希）"""
        password_hash = hash_password(password)
        return await self.create(
            username=username,
            password_hash=password_hash,
            email=email,
            **kwargs
        )
    
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """验证密码"""
        return verify_password(plain_password, password_hash)
    
    async def change_password(self, user_id: int, new_password: str) -> bool:
        """修改密码"""
        password_hash = hash_password(new_password)
        affected = await self.update(user_id, password_hash=password_hash)
        return affected > 0


# 全局单例
user_repo = UserRepository()
