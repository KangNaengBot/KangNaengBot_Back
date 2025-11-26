"""
POST /profiles - 프로필 저장
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from utils.dependencies import get_current_user
from services.profile_service import ProfileService, get_profile_service

router = APIRouter()


class ProfileRequest(BaseModel):
    """프로필 저장/수정 요청 (부분 업데이트 가능)"""
    profile_name: Optional[str] = Field(None, description="프로필 이름")
    student_id: Optional[str] = Field(None, description="학번")
    college: Optional[str] = Field(None, description="단과대학 정보")
    department: Optional[str] = Field(None, description="학부/학과")
    major: Optional[str] = Field(None, description="전공 정보")
    current_grade: Optional[int] = Field(None, ge=1, le=5, description="현재 학년 (1-5)")
    current_semester: Optional[int] = Field(None, ge=1, le=2, description="현재 학기 (1-2)")


class ProfileResponse(BaseModel):
    """프로필 저장 응답"""
    id: int
    user_id: int
    profile_name: str
    student_id: str
    college: str
    department: str
    major: str
    current_grade: int
    current_semester: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/", response_model=ProfileResponse)
async def save_profile(
    profile_data: ProfileRequest,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    프로필 정보를 저장/수정합니다.
    
    JWT 토큰에서 user_id를 자동으로 추출하여 사용합니다.
    
    **신규 생성**: 모든 필드 필수
    **기존 수정**: 변경하고 싶은 필드만 보내면 됩니다 (부분 업데이트)
    
    Headers:
        Authorization: Bearer {access_token}
    
    Request Body (모두 선택):
        profile_name: 프로필 이름
        student_id: 학번
        college: 단과대학 정보
        department: 학부/학과
        major: 전공 정보
        current_grade: 현재 학년 (1-5)
        current_semester: 현재 학기 (1-2)
    
    Examples:
        # 전체 생성
        {
          "profile_name": "홍길동",
          "student_id": "20210001",
          "college": "공과대학",
          "department": "컴퓨터공학부",
          "major": "소프트웨어전공",
          "current_grade": 4,
          "current_semester": 2
        }
        
        # 이름만 수정
        {
          "profile_name": "새이름"
        }
        
        # 학년/학기만 수정
        {
          "current_grade": 4,
          "current_semester": 1
        }
    
    Returns:
        저장된 프로필 정보
    """
    try:
        # JWT에서 user_id 추출
        user_id = int(current_user["id"])
        
        # 서비스를 통해 프로필 저장 (부분 업데이트 지원)
        profile = profile_service.save_profile(
            user_id=user_id,
            profile_name=profile_data.profile_name,
            student_id=profile_data.student_id,
            college=profile_data.college,
            department=profile_data.department,
            major=profile_data.major,
            current_grade=profile_data.current_grade,
            current_semester=profile_data.current_semester
        )
        
        # 응답 반환
        return ProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
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
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save profile: {str(e)}"
        )
