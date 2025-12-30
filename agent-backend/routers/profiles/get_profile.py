"""
GET /profiles - 프로필 조회
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from utils.dependencies import get_current_user
from services.profile_service import ProfileService, get_profile_service
from .save_profile import ProfileResponse

router = APIRouter()


@router.get("/", response_model=Optional[ProfileResponse])
async def get_profile(
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    현재 로그인된 사용자의 프로필을 조회합니다.
    
    Headers:
        Authorization: Bearer {access_token}
    
    Returns:
        프로필 정보 (없으면 null)
    """
    try:
        # JWT에서 user_id 추출
        user_id = int(current_user["id"])
        
        # 서비스를 통해 프로필 조회
        profile = profile_service.get_profile(user_id)
        
        if not profile:
            return None
        
        # 응답 반환 - user_sid를 id로 사용
        return ProfileResponse(
            id=str(profile.user_sid) if profile.user_sid else str(profile.user_id),
            profile_name=profile.profile_name,
            student_id=profile.student_id,
            college=profile.college,
            department=profile.department,
            major=profile.major,
            current_grade=profile.current_grade,
            current_semester=profile.current_semester,
            created_at=profile.created_at.isoformat() if profile.created_at else None,
            updated_at=profile.updated_at.isoformat() if profile.updated_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get profile: {str(e)}"
        )
