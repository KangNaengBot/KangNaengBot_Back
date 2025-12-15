"""
GET /auth/check-user - 사용자 로그인 이력 확인
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from utils.jwt import verify_token
from routers.database import get_db
from .helpers import check_user_exists_by_email, check_user_exists_by_google_id

router = APIRouter()
security = HTTPBearer()


@router.get("/check-user")
async def check_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    email: Optional[str] = Query(None, description="확인할 이메일 주소"),
    google_id: Optional[str] = Query(None, description="확인할 Google ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자가 로그인한 적이 있는지 확인
    
    Headers:
        Authorization: Bearer {access_token}
    
    Query Parameters:
        email: (선택) 확인할 이메일 주소
        google_id: (선택) 확인할 Google ID
    
    Note:
        email 또는 google_id 중 하나는 반드시 제공되어야 합니다.
    
    Returns:
        {
            "exists": bool,  # 사용자가 존재하면 True
            "checked_by": str  # "email" 또는 "google_id"
        }
    """
    # JWT 토큰 검증
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    # email 또는 google_id 중 하나는 필수
    if not email and not google_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'email' or 'google_id' parameter is required"
        )
    
    # email로 확인
    if email:
        exists = await check_user_exists_by_email(db, email)
        return {
            "exists": exists,
            "checked_by": "email",
            "value": email
        }
    
    # google_id로 확인
    if google_id:
        exists = await check_user_exists_by_google_id(db, google_id)
        return {
            "exists": exists,
            "checked_by": "google_id",
            "value": google_id
        }

