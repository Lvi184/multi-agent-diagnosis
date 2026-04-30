#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断数据访问层
"""
from typing import Optional, List
from app.models import DiagnosisSession, DiagnosisRecord
from .base_repo import BaseRepository


class DiagnosisSessionRepository(BaseRepository):
    """诊断会话 Repository"""
    
    def __init__(self):
        super().__init__(DiagnosisSession)
    
    async def get_by_session_id(self, session_id: str) -> Optional[DiagnosisSession]:
        """根据 session_id 获取会话"""
        return await self.model.filter(session_id=session_id, is_deleted=False).first()
    
    async def get_user_sessions(self, user_id: int, limit: int = 20) -> List[DiagnosisSession]:
        """获取用户的所有会话"""
        return await self.model.filter(
            user_id=user_id, 
            is_deleted=False
        ).order_by('-created_at').limit(limit).all()
    
    async def update_collected_info(self, session_id: str, **kwargs) -> bool:
        """更新收集到的信息（症状、病史等）"""
        affected = await self.model.filter(session_id=session_id, is_deleted=False).update(**kwargs)
        return affected > 0
    
    async def mark_completed(self, session_id: str) -> bool:
        """标记会话已完成"""
        affected = await self.model.filter(session_id=session_id, is_deleted=False).update(status="completed")
        return affected > 0


class DiagnosisRecordRepository(BaseRepository):
    """诊断记录 Repository"""
    
    def __init__(self):
        super().__init__(DiagnosisRecord)
    
    async def get_by_session_id(self, session_id: str) -> Optional[DiagnosisRecord]:
        """根据 session_id 获取诊断记录"""
        return await self.model.filter(session_id=session_id, is_deleted=False).first()
    
    async def get_user_records(self, user_id: int, limit: int = 20) -> List[DiagnosisRecord]:
        """获取用户的所有诊断记录"""
        return await self.model.filter(
            user_id=user_id, 
            is_deleted=False
        ).order_by('-created_at').limit(limit).all()
    
    async def get_by_risk_level(self, risk_level: str, limit: int = 50) -> List[DiagnosisRecord]:
        """按风险等级筛选记录"""
        return await self.model.filter(
            risk_level=risk_level, 
            is_deleted=False
        ).order_by('-created_at').limit(limit).all()


# 全局单例
session_repo = DiagnosisSessionRepository()
record_repo = DiagnosisRecordRepository()
