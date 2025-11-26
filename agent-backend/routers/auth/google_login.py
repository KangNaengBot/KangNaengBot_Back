"""
GET /auth/google/login - Google OAuth 로그인 시작
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import config
from .oauth_config import oauth

router = APIRouter()


@router.get("/google/login")
async def google_login(request: Request, redirect_uri: Optional[str] = None):
    """
    Google OAuth 로그인 URL로 리다이렉트
    
    Query Parameters:
        redirect_uri: (선택) 로그인 후 돌아갈 프론트엔드 URL
                      예: https://gangnangbot.vercel.app/auth/callback?from=api-test
    
    Authlib이 자동으로 State 생성 및 세션 저장을 처리합니다.
    """
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="OAuth credentials not configured"
        )
    
    # 프론트엔드 redirect_uri를 세션에 저장 (콜백에서 사용)
    if redirect_uri:
        request.session['frontend_redirect_uri'] = redirect_uri
    
    # Google OAuth redirect_uri (백엔드 콜백 URL)
    oauth_redirect_uri = config.OAUTH_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, oauth_redirect_uri)
