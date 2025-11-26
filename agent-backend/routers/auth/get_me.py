"""
GET /auth/me - 현재 로그인된 사용자 정보 조회
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from utils.jwt import verify_token
from routers.database import get_db
from .helpers import get_user_by_id

router = APIRouter()
security = HTTPBearer()


@router.get("/me")
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    현재 로그인된 사용자 정보 조회
    
    Headers:
        Authorization: Bearer {access_token}
    
    Returns:
        사용자 정보 (id: UUID, email, name 등)
    """
    # JWT 검증
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # DB에서 사용자 정보 조회
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 프론트엔드용 응답: sid를 id로 변경 (UUID 형식)
    return {
        "id": user["sid"],  # UUID (프론트엔드에서 사용)
        "email": user["email"],
        "name": user["name"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"]
    }
