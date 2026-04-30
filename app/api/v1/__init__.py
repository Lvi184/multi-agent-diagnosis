#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 接口集合
"""
from .base import router as base_router
from .auth import router as auth_router
from .dialogue import router as dialogue_router
from .diagnosis import router as diagnosis_router

__all__ = [
    'base_router',
    'auth_router',
    'dialogue_router',
    'diagnosis_router',
]
