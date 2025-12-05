"""
FastAPI Dependencies - 인증 및 유저 정보
"""
from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import random
from utils.jwt import verify_token
from routers.database import get_db
from routers.auth.helpers import get_user_by_id  # 순환 import 방지

# HTTPBearer security scheme (Swagger UI용) - auto_error=False로 선택적 인증
security = HTTPBearer(auto_error=False)


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
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
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


async def get_current_user_or_guest(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    인증된 사용자 또는 게스트 사용자 정보 반환
    
    - Authorization 헤더가 있으면: 인증된 사용자 정보 반환
    - Authorization 헤더가 없으면: 게스트 사용자 정보 반환 (user_id 요청에서 추출 또는 생성)
    
    Returns:
        사용자 정보 딕셔너리
        - id: 사용자 ID (게스트는 랜덤 생성된 ID)
        - is_guest: 게스트 여부
    """
    # 인증 토큰이 있으면 검증
    if credentials:
        try:
            token = credentials.credentials
            payload = verify_token(token)
            
            if payload and payload.get("user_id"):
                user_id = int(payload["user_id"])
                user = await get_user_by_id(db, str(user_id))
                if user:
                    user["id"] = int(user["id"])
                    user["is_guest"] = False
                    return user
        except Exception as e:
            print(f"[Auth] Token verification failed, falling back to guest: {e}")
    
    # 게스트 모드: 요청 body에서 user_id 추출하거나 새로 생성
    # Body는 이미 소비되었을 수 있으므로 랜덤 ID 생성
    guest_id = random.randint(100000000, 999999999)
    
    return {
        "id": guest_id,
        "is_guest": True,
        "email": None,
        "name": "Guest"
    }
