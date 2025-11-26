"""
FastAPI Dependencies - 인증 및 유저 정보
"""
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from utils.jwt import verify_token
from routers.database import get_db
from routers.auth.helpers import get_user_by_id  # 순환 import 방지

# HTTPBearer security scheme (Swagger UI용)
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    JWT 토큰에서 현재 로그인된 사용자 ID를 추출
    
    Args:
        credentials: HTTPBearer로부터 받은 인증 정보
        
    Returns:
        user_id: 정수형 사용자 ID
        
    Raises:
        HTTPException: 인증 실패 시
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # 문자열이든 숫자든 항상 int로 변환
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user_id format in token")


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    현재 로그인된 사용자의 전체 정보를 DB에서 조회
    
    Returns:
        사용자 정보 딕셔너리
        - id: 내부 BIGINT ID (서비스/레포지토리에서 사용)
        - sid: UUID (프론트엔드 노출용)
    """
    # DB에는 문자열로 전달
    user = await get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 내부 ID는 정수로 유지 (DB 조회용)
    user["id"] = int(user["id"])
    return user
