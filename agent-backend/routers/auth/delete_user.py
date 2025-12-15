"""
DELETE /auth/me - 회원 탈퇴
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from utils.jwt import verify_token
from routers.database import get_db
from .helpers import delete_user, get_user_by_id

router = APIRouter()
security = HTTPBearer()


@router.delete("/me")
async def delete_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    회원 탈퇴 (Soft Delete)
    
    Headers:
        Authorization: Bearer {access_token}
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # 사용자 존재 확인 (실제 존재하는지)
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 탈퇴 처리 (int로 변환하여 전달)
    success = await delete_user(db, int(user_id))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
        
    return {"status": "success", "message": "User deleted successfully"}
