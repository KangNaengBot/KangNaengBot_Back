"""
GET /auth/google/callback - Google OAuth 콜백 처리
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from routers.database import get_db
from services.issue_tokens_service import issue_tokens
from .oauth_config import oauth
from .helpers import upsert_user
import config

router = APIRouter()


@router.get("/google/callback")
async def google_callback(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Google OAuth 콜백 처리
    
    Google로부터 인증 코드를 받아 토큰으로 교환하고,
    사용자 정보를 DB에 저장한 후 프론트엔드로 리다이렉트합니다.
    
    Access Token(1시간)과 Refresh Token(7일)을 함께 발급합니다.
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
        # name이 없으면 email에서 추출, email도 없으면 기본값
        name = user_info.get('name') or (email.split('@')[0] if email else 'User')
        
        # DB에 사용자 정보 저장/업데이트
        user_id = await upsert_user(db, google_id, email, name)
        
        # Access Token(1시간) + Refresh Token(7일) 발급
        access_token, refresh_token = issue_tokens(user_id, email)
        
        # 세션에서 프론트엔드 redirect_uri 가져오기 (없으면 기본값 사용)
        frontend_redirect = request.session.get('frontend_redirect_uri')
        if not frontend_redirect:
            # 기본값: config에 설정된 프론트엔드 URL
            frontend_redirect = f"{config.FRONTEND_URL}/auth/callback"
        
        # 세션에서 redirect_uri 제거 (일회성)
        request.session.pop('frontend_redirect_uri', None)
        
        # URL 파라미터 생성 (특수문자 인코딩)
        
        # 기존 쿼리 파라미터 확인
        separator = '&' if '?' in frontend_redirect else '?'
        
        # 파라미터 생성 (URL 인코딩 자동 처리)
        params = urlencode({
            'token': access_token,  # Access Token만 URL로 전달
            'email': email or '',
            'name': name
        })
        
        # RedirectResponse 생성
        redirect_response = RedirectResponse(
            url=f"{frontend_redirect}{separator}{params}"
        )
        
        # Refresh Token을 HttpOnly 쿠키로 설정 (7일, Sliding Session)
        redirect_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,        # JavaScript 접근 불가 (XSS 방어)
            secure=True,          # HTTPS에서만 전송
            samesite="lax",       # CSRF 방어
            max_age=604800,       # 7일 (초 단위)
            path="/auth"          # /auth 경로에서만 사용
        )
        
        return redirect_response
        
    except Exception as e:
        # 에러 발생 시 프론트엔드 로그인 페이지로 리다이렉트
        frontend_url = config.FRONTEND_URL
        error_message = str(e).replace(" ", "_")  # URL 안전하게
        return RedirectResponse(
            url=f"{frontend_url}/login?error={error_message}"
        )
