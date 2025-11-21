"""
GET /auth/google/callback - Google OAuth 콜백 처리
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from routers.database import get_db
from utils.jwt import create_access_token
from .oauth_config import oauth
from .helpers import upsert_user

router = APIRouter()


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Google OAuth 콜백 처리
    
    Google로부터 인증 코드를 받아 토큰으로 교환하고,
    사용자 정보를 DB에 저장한 후 JWT 토큰을 반환합니다.
    """
    try:
        # 토큰 교환 및 검증 (Authlib이 State 검증 자동 수행)
        token = await oauth.google.authorize_access_token(request)
        
        # 사용자 정보 가져오기
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        # DB에 사용자 정보 저장/업데이트
        user_id = await upsert_user(db, google_id, email, name)
        
        # JWT 액세스 토큰 생성
        access_token = create_access_token(data={"user_id": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": email,
                "name": name
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback failed: {str(e)}"
        )
