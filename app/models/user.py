#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型
"""
from tortoise import fields
from .base import BaseModel


class UserRole:
    """用户角色枚举"""
    USER = "user"           # 普通用户
    ADMIN = "admin"         # 管理员
    DOCTOR = "doctor"       # 医生


class User(BaseModel):
    """用户表"""
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password_hash = fields.CharField(max_length=255, description="密码哈希")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    nickname = fields.CharField(max_length=50, null=True, description="昵称")
    avatar = fields.CharField(max_length=255, null=True, description="头像URL")
    role = fields.CharField(max_length=20, default=UserRole.USER, description="角色")
    is_active = fields.BooleanField(default=True, description="是否激活")
    
    class Meta:
        table = "users"
        table_description = "用户表"
    
    def __str__(self):
        return f"User(id={self.id}, username={self.username})"


class RefreshToken(BaseModel):
    """刷新令牌表"""
    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens")
    token = fields.CharField(max_length=512, unique=True, description="刷新令牌")
    expires_at = fields.DatetimeField(description="过期时间")
    
    class Meta:
        table = "refresh_tokens"
        table_description = "JWT刷新令牌表"
