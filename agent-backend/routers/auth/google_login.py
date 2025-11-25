"""
GET /auth/google/login - Google OAuth 로그인 시작
"""
from fastapi import APIRouter, HTTPException, Request, Query
import config
from .oauth_config import oauth

router = APIRouter()


@router.get("/google/login")
async def google_login(request: Request, redirect_uri: str = Query(None)):
    """
    Google OAuth 로그인 URL로 리다이렉트
    
    Args:
        redirect_uri: 로그인 완료 후 리다이렉트할 URI
    
    Authlib이 자동으로 State 생성 및 세션 저장을 처리합니다.
    """
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="OAuth credentials not configured"
        )
    
    # 사용자가 지정한 redirect_uri가 있으면 세션에 저장
    if redirect_uri:
        request.session['oauth_redirect_uri'] = redirect_uri
    
    # OAuth 콜백 URI는 항상 고정 (Google OAuth 설정에 등록된 URI)
    oauth_redirect_uri = config.OAUTH_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, oauth_redirect_uri)
