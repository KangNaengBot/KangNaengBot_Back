"""
POST /auth/logout - 로그아웃

단일 책임: Refresh Token 쿠키를 삭제하여 로그아웃 처리합니다.
"""
from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter()


class LogoutResponse(BaseModel):
    """로그아웃 응답"""
    message: str


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response):
    """
    로그아웃
    
    Refresh Token 쿠키를 삭제하여 사용자를 로그아웃시킵니다.
    Access Token은 클라이언트가 삭제해야 합니다.
    
    Response:
        message: 로그아웃 성공 메시지
        
    Response Cookie:
        refresh_token: 빈 값 (Max-Age=0으로 즉시 만료)
    
    Note:
        DB를 사용하지 않으므로 쿠키 삭제만으로 로그아웃 처리됩니다.
        기존 Refresh Token은 7일 후 자동으로 만료됩니다.
    
    Example:
        POST /auth/logout
        
        Response:
        {
            "message": "Logged out successfully"
        }
        + Set-Cookie: refresh_token=; Max-Age=0
    """
    # Refresh Token 쿠키 삭제
    response.set_cookie(
        key="refresh_token",
        value="",             # 빈 값
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=0,            # 즉시 만료
        path="/auth"
    )
    
    return LogoutResponse(
        message="Logged out successfully"
    )
