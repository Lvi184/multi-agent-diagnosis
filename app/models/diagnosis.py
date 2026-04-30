#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断相关模型 - 会话、诊断记录
"""
from tortoise import fields
from .base import BaseModel


class DiagnosisSession(BaseModel):
    """诊断会话表 - 每一轮对话对应一个会话"""
    user = fields.ForeignKeyField("models.User", related_name="sessions", null=True, description="用户ID（未登录用户可为空）")
    session_id = fields.CharField(max_length=100, unique=True, description="会话ID")
    status = fields.CharField(max_length=20, default="collecting", description="状态: collecting/diagnosing/completed")
    age = fields.IntField(null=True, description="年龄")
    gender = fields.CharField(max_length=10, null=True, description="性别")
    
    # 已收集的信息
    symptoms = fields.JSONField(default=list, description="症状列表")
    duration = fields.CharField(max_length=100, null=True, description="持续时间")
    medical_history = fields.TextField(null=True, description="既往病史")
    medication_history = fields.TextField(null=True, description="用药史")
    has_suicide_risk = fields.BooleanField(default=None, null=True, description="是否有自杀/自伤风险")
    
    # 量表分数
    phq9_score = fields.IntField(null=True, description="PHQ-9 分数")
    gad7_score = fields.IntField(null=True, description="GAD-7 分数")
    
    # 对话阶段
    conversation_stage = fields.CharField(max_length=30, default="init", description="对话阶段")
    
    # 量表答题记录
    phq9_answers = fields.JSONField(default=list, description="PHQ-9 每题答案")
    gad7_answers = fields.JSONField(default=list, description="GAD-7 每题答案")
    
    # 对话进度追踪
    stage_step_count = fields.IntField(default=0, description="当前阶段对话步数")
    
    # 对话历史
    chat_history = fields.JSONField(default=list, description="对话历史")
    
    class Meta:
        table = "diagnosis_sessions"
        table_description = "诊断会话表"
    
    def __str__(self):
        return f"DiagnosisSession(id={self.id}, session_id={self.session_id})"


class DiagnosisRecord(BaseModel):
    """诊断记录表 - 保存每次完整的诊断报告"""
    user = fields.ForeignKeyField("models.User", related_name="diagnoses", null=True, description="用户ID")
    session = fields.OneToOneField("models.DiagnosisSession", related_name="record", description="会话ID")
    
    # 诊断结果
    suspected_diagnosis = fields.JSONField(default=list, description="疑似诊断列表")
    risk_level = fields.CharField(max_length=20, description="风险等级")
    risk_types = fields.JSONField(default=list, description="风险类型")
    recommendations = fields.JSONField(default=list, description="建议列表")
    evidence_chain = fields.JSONField(default=list, description="证据链")
    
    # 完整报告
    full_report = fields.JSONField(null=True, description="完整诊断报告")
    structured_report = fields.JSONField(null=True, description="结构化报告")
    
    # 元数据
    agent_traces = fields.JSONField(default=list, description="Agent执行轨迹")
    diagnosis_time_ms = fields.IntField(null=True, description="诊断耗时(毫秒)")
    model_version = fields.CharField(max_length=50, null=True, description="模型版本")
    
    # 用户反馈
    user_feedback = fields.TextField(null=True, description="用户反馈")
    is_helpful = fields.BooleanField(null=True, description="是否有帮助")
    
    class Meta:
        table = "diagnosis_records"
        table_description = "诊断记录表"
    
    def __str__(self):
        return f"DiagnosisRecord(id={self.id}, risk_level={self.risk_level})"
