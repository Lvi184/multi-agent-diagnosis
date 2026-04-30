#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础 Repository - 封装通用 CRUD 操作
"""
from typing import TypeVar, Type, Optional, List, Dict, Any
from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)


class BaseRepository:
    """基础 Repository 类"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """根据 ID 获取"""
        return await self.model.filter(id=id, is_deleted=False).first()
    
    async def create(self, **kwargs) -> ModelType:
        """创建"""
        return await self.model.create(**kwargs)
    
    async def update(self, id: int, **kwargs) -> int:
        """更新"""
        return await self.model.filter(id=id, is_deleted=False).update(**kwargs)
    
    async def delete(self, id: int) -> int:
        """软删除"""
        return await self.model.filter(id=id).update(is_deleted=True)
    
    async def hard_delete(self, id: int) -> int:
        """硬删除（从数据库彻底删除）"""
        return await self.model.filter(id=id).delete()
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """列出所有"""
        return await self.model.filter(is_deleted=False).limit(limit).offset(offset).all()
    
    async def count(self) -> int:
        """统计总数"""
        return await self.model.filter(is_deleted=False).count()
