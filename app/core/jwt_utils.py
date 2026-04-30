#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT 工具 - 不依赖 PyJWT，用 Python 内置库实现，避免版本冲突
"""
import json
import base64
import hmac
import hashlib
import time
from typing import Optional, Dict, Any


def b64url_encode(data: bytes) -> str:
    """Base64 URL 编码"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def b64url_decode(data: str) -> bytes:
    """Base64 URL 解码"""
    padding = '=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_jwt(payload: Dict[str, Any], secret_key: str, algorithm: str = "HS256") -> str:
    """创建 JWT Token"""
    # Header
    header = {"typ": "JWT", "alg": algorithm}
    header_json = json.dumps(header, separators=(',', ':')).encode()
    
    # Payload
    payload_json = json.dumps(payload, separators=(',', ':')).encode()
    
    # Base64 编码
    header_b64 = b64url_encode(header_json)
    payload_b64 = b64url_encode(payload_json)
    
    # 签名
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(
        secret_key.encode(),
        signing_input,
        hashlib.sha256
    ).digest()
    signature_b64 = b64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt(token: str, secret_key: str, algorithms: list = None) -> Optional[Dict[str, Any]]:
    """解码并验证 JWT Token，失败返回 None"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        
        # 重新计算签名，验证有效性
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_signature = hmac.new(
            secret_key.encode(),
            signing_input,
            hashlib.sha256
        ).digest()
        actual_signature = b64url_decode(signature_b64)
        
        # 比较签名（防时序攻击）
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None
        
        # 解码 payload
        payload_json = b64url_decode(payload_b64)
        payload = json.loads(payload_json)
        
        # 检查过期时间
        if 'exp' in payload and time.time() > payload['exp']:
            return None
        
        return payload
    except Exception:
        return None
