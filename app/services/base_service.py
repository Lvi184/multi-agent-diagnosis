#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础 Service 类
"""
from typing import Generic, TypeVar, Type, Optional, List
from app.repositories import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)


class BaseService(Generic[RepoType]):
    """基础 Service 类"""
    
    def __init__(self, repository: RepoType):
        self.repo = repository
    
    async def get_by_id(self, id: int):
        return await self.repo.get_by_id(id)
    
    async def create(self, **kwargs):
        return await self.repo.create(**kwargs)
    
    async def update(self, id: int, **kwargs):
        return await self.repo.update(id, **kwargs)
    
    async def delete(self, id: int):
        return await self.repo.delete(id)
    
    async def list_all(self, limit: int = 100, offset: int = 0):
        return await self.repo.list_all(limit, offset)
    
    async def count(self):
        return await self.repo.count()
