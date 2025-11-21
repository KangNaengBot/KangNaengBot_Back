"""
GET /auth/google/login - Google OAuth 로그인 시작
"""
from fastapi import APIRouter, HTTPException, Request
import config
from .oauth_config import oauth

router = APIRouter()


@router.get("/google/login")
async def google_login(request: Request):
    """
    Google OAuth 로그인 URL로 리다이렉트
    
    Authlib이 자동으로 State 생성 및 세션 저장을 처리합니다.
    """
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="OAuth credentials not configured"
        )
    
    redirect_uri = config.OAUTH_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)
