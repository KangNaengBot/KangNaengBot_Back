"""
POST /auth/generate-token - 테스트용 JWT 토큰 생성
"""
from fastapi import APIRouter
from pydantic import BaseModel

from utils.jwt import create_access_token

router = APIRouter()


class GenerateTokenResponse(BaseModel):
    """토큰 생성 응답"""
    access_token: str
    token_type: str
    user_id: str
    note: str


@router.post("/generate-token", response_model=GenerateTokenResponse)
async def generate_test_token(user_id: str):
    """
    테스트용 JWT 토큰 생성
    
    ⚠️ 개발/테스트 전용 엔드포인트입니다.
    프로덕션 환경에서는 비활성화해야 합니다.
    
    Query Parameters:
        user_id: 토큰에 포함할 사용자 ID
    
    Returns:
        access_token: 생성된 JWT 토큰
        token_type: "bearer"
    
    Example:
        POST /auth/generate-token?user_id=1
    """
    # JWT 토큰 생성
    access_token = create_access_token(data={"user_id": user_id})
    
    return GenerateTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        note="⚠️ 테스트용 토큰입니다. Swagger UI의 'Authorize' 버튼을 클릭하여 사용하세요."
    )
