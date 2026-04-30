#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断接口 - 历史记录、详情查看
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.repositories import record_repo
from app.core.deps import get_current_user
from app.models import User

router = APIRouter()


class DiagnosisRecordItem(BaseModel):
    """诊断记录项"""
    id: int
    session_id: str
    suspected_diagnosis: List[str]
    risk_level: str
    created_at: Any


@router.get("/records", response_model=List[DiagnosisRecordItem], summary="获取我的诊断记录")
async def get_my_records(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
):
    """
    获取当前用户的所有历史诊断记录（需要登录）
    """
    records = await record_repo.get_user_records(user.id, limit=limit)
    return [
        {
            "id": r.id,
            "session_id": r.session.session_id,
            "suspected_diagnosis": r.suspected_diagnosis,
            "risk_level": r.risk_level,
            "created_at": r.created_at,
        }
        for r in records
    ]


@router.get("/records/{record_id}", summary="获取诊断记录详情")
async def get_record_detail(
    record_id: int,
    user: User = Depends(get_current_user),
):
    """
    获取单条诊断记录的完整详情（需要登录）
    """
    record = await record_repo.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断记录不存在",
        )
    
    # 权限校验：只能看自己的记录
    if record.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此记录",
        )
    
    return {
        "id": record.id,
        "session_id": record.session.session_id,
        "suspected_diagnosis": record.suspected_diagnosis,
        "risk_level": record.risk_level,
        "risk_types": record.risk_types,
        "recommendations": record.recommendations,
        "evidence_chain": record.evidence_chain,
        "structured_report": record.structured_report,
        "created_at": record.created_at,
        "user_feedback": record.user_feedback,
        "is_helpful": record.is_helpful,
    }


@router.post("/records/{record_id}/feedback", summary="提交诊断反馈")
async def submit_feedback(
    record_id: int,
    feedback: str,
    is_helpful: bool = None,
    user: User = Depends(get_current_user),
):
    """
    对诊断结果提交反馈（是否有用、具体意见）
    
    请求示例：
    {
        "feedback": "报告很详细，建议很有帮助",
        "is_helpful": true
    }
    """
    record = await record_repo.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断记录不存在",
        )
    
    if record.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此记录",
        )
    
    await record_repo.update(
        record_id,
        user_feedback=feedback,
        is_helpful=is_helpful,
    )
    
    return {
        "success": True,
        "message": "反馈已提交，感谢你的意见！",
    }


@router.get("/stats/summary", summary="获取诊断统计（管理员）")
async def get_diagnosis_stats(user: User = Depends(get_current_user)):
    """
    获取诊断统计数据（仅管理员可见）
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问",
        )
    
    total = await record_repo.count()
    high_risk = await record_repo.get_by_risk_level("high")
    medium_risk = await record_repo.get_by_risk_level("medium")
    low_risk = await record_repo.get_by_risk_level("low")
    
    return {
        "total_diagnoses": total,
        "risk_distribution": {
            "high": len(high_risk),
            "medium": len(medium_risk),
            "low": len(low_risk),
        },
    }
