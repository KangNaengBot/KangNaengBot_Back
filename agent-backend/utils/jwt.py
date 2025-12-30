"""
JWT 토큰 유틸리티
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import config


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성 (1시간)

    Args:
        user_id: 사용자 ID (토큰에 포함할 유일한 식별자)
        expires_delta: 만료 시간 (기본값: config.JWT_EXPIRATION_HOURS)

    Returns:
        JWT 토큰 문자열
        
    Note:
        보안 및 토큰 크기 최소화를 위해 user_id만 포함합니다.
        이메일 등 추가 정보는 DB에서 조회하세요.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRATION_HOURS)

    to_encode = {
        "user_id": user_id,
        "type": "access",  # 토큰 타입 구분
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 검증 및 디코딩

    Args:
        token: JWT 토큰 문자열

    Returns:
        디코딩된 payload (dict) 또는 None (검증 실패 시)
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_refresh_token(user_id: int) -> str:
    """
    JWT 리프레시 토큰 생성 (7일)
    
    Sliding Session 방식: 사용할 때마다 새로 발급되어 7일 연장
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        JWT Refresh Token 문자열
    """
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode = {
        "user_id": user_id,
        "type": "refresh",  # Refresh Token 구분
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Refresh Token 전용 검증
    
    Args:
        token: Refresh Token 문자열
        
    Returns:
        디코딩된 payload (dict) 또는 None (검증 실패 시)
        
    Note:
        type이 "refresh"인지 확인합니다.
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        
        # Refresh Token인지 확인
        if payload.get("type") != "refresh":
            return None
            
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def issue_token_pair(user_id: int) -> tuple[str, str]:
    """
    Access Token + Refresh Token 쌍 발급
    
    최초 로그인 및 토큰 재발급 시 동일하게 사용됩니다.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        (access_token, refresh_token) 튜플
        
    Example:
        access_token, refresh_token = issue_token_pair(user_id=123)
        
    Note:
        - Access Token: 1시간 유효 (user_id만 포함)
        - Refresh Token: 7일 유효 (Sliding Session)
    """
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    return access_token, refresh_token
