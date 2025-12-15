"""
POST /auth/refresh - Refresh Token으로 새 토큰 발급

단일 책임: Refresh Token을 받아 새 Access Token과 새 Refresh Token을 발급합니다.
"""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from services.refresh_tokens_service import refresh_tokens

router = APIRouter()


class RefreshTokenResponse(BaseModel):
    """토큰 갱신 응답"""
    access_token: str
    token_type: str


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: Request, response: Response):
    """
    Refresh Token으로 새 토큰 발급 (Sliding Session)
    
    Refresh Token이 유효하면 새로운 Access Token과 Refresh Token을 발급합니다.
    사용할 때마다 7일이 연장되는 Sliding Session 방식입니다.
    
    Cookie (Required):
        refresh_token: Refresh Token (HttpOnly 쿠키)
    
    Response:
        access_token: 새로운 Access Token (1시간)
        
    Response Cookie:
        refresh_token: 새로운 Refresh Token (7일, HttpOnly)
    
    Errors:
        401: Refresh Token이 없거나 무효한 경우
    
    Example:
        POST /auth/refresh
        Cookie: refresh_token=eyJ0eXAiOiJKV1QiLCJhbGc...
        
        Response:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer"
        }
        + Set-Cookie: refresh_token=NEW_TOKEN; HttpOnly; Secure; ...
    """
    # 쿠키에서 Refresh Token 추출
    refresh_token_value = request.cookies.get("refresh_token")
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=401,
            detail="No refresh token provided"
        )
    
    try:
        # 새 토큰 발급 (Sliding Session)
        new_access_token, new_refresh_token = refresh_tokens(refresh_token_value)
        
        # HttpOnly 쿠키로 새 Refresh Token 설정
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,        # JavaScript 접근 불가 (XSS 방어)
            secure=True,          # HTTPS에서만 전송
            samesite="lax",       # CSRF 방어
            max_age=604800,       # 7일 (초 단위)
            path="/auth"          # /auth 경로에서만 사용
        )
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            token_type="bearer"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
