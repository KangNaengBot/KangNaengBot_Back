"""
ProfileService - 프로필 비즈니스 로직
"""
from typing import Optional

from domain.entities.profile import Profile
from domain.repositories.profile_repository import ProfileRepository


class ProfileService:
    """프로필 관리 서비스"""
    
    def __init__(self, profile_repo: ProfileRepository):
        """
        Args:
            profile_repo: Profile Repository
        """
        self.repo = profile_repo
    
    def save_profile(
        self,
        user_id: int,
        profile_name: Optional[str] = None,
        student_id: Optional[str] = None,
        college: Optional[str] = None,
        department: Optional[str] = None,
        major: Optional[str] = None,
        current_grade: Optional[int] = None,
        current_semester: Optional[int] = None
    ) -> Profile:
        """
        프로필 저장 (upsert) - 부분 업데이트 지원
        
        제공된 필드만 업데이트하고, None인 필드는 기존 값 유지합니다.
        프로필이 없으면 모든 필드가 필수입니다.
        
        Args:
            user_id: 사용자 ID
            profile_name: 프로필 이름 (선택)
            student_id: 학번 (선택)
            college: 단과대학 (선택)
            department: 학과 (선택)
            major: 전공 (선택)
            current_grade: 현재 학년 (선택)
            current_semester: 현재 학기 (선택)
            
        Returns:
            저장된 Profile 엔티티
            
        Raises:
            ValueError: 신규 프로필 생성 시 필수 필드 누락
        """
        # 기존 프로필 조회
        existing_profile = self.repo.find_by_user_id(user_id)
        
        if existing_profile:
            # 기존 프로필 업데이트 - 제공된 필드만 업데이트
            updated_profile = Profile(
                id=existing_profile.id,
                user_id=user_id,
                profile_name=profile_name if profile_name is not None else existing_profile.profile_name,
                student_id=student_id if student_id is not None else existing_profile.student_id,
                college=college if college is not None else existing_profile.college,
                department=department if department is not None else existing_profile.department,
                major=major if major is not None else existing_profile.major,
                current_grade=current_grade if current_grade is not None else existing_profile.current_grade,
                current_semester=current_semester if current_semester is not None else existing_profile.current_semester,
                created_at=existing_profile.created_at,
                updated_at=existing_profile.updated_at
            )
            saved_profile = self.repo.save(updated_profile)
            print(f"[ProfileService] Profile updated for user_id={user_id}")
        else:
            # 신규 프로필 생성 - 모든 필드 필수
            if not all([profile_name, student_id, college, department, major, 
                       current_grade is not None, current_semester is not None]):
                raise ValueError(
                    "신규 프로필 생성 시 모든 필드가 필요합니다: "
                    "profile_name, student_id, college, department, major, current_grade, current_semester"
                )
            
            profile = Profile.create(
                user_id=user_id,
                profile_name=profile_name,
                student_id=student_id,
                college=college,
                department=department,
                major=major,
                current_grade=current_grade,
                current_semester=current_semester
            )
            saved_profile = self.repo.save(profile)
            print(f"[ProfileService] Profile created for user_id={user_id}")
        
        return saved_profile
    
    def get_profile(self, user_id: int) -> Optional[Profile]:
        """
        사용자 프로필 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Profile 엔티티 (없으면 None)
        """
        return self.repo.find_by_user_id(user_id)


# Dependency Injection을 위한 싱글톤 팩토리
_profile_service_instance: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    """
    ProfileService 싱글톤 인스턴스 반환
    
    FastAPI Dependency로 사용됩니다.
    """
    global _profile_service_instance
    
    if _profile_service_instance is None:
        from supabase import create_client
        from urllib.parse import urlparse
        import config
        
        # DATABASE_URL에서 Supabase URL 추출
        db_url = config.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL is not configured")
        
        parsed = urlparse(db_url)
        username = parsed.username
        
        if username and '.' in username:
            project_ref = username.split('.', 1)[1]
            supabase_url = f"https://{project_ref}.supabase.co"
        else:
            raise ValueError("Invalid DATABASE_URL format: cannot extract project_ref")
        
        # API 키는 config에서 가져오기
        supabase_key = config.SUPABASE_KEY
        if not supabase_key:
            raise ValueError("SUPABASE_KEY (DATABASE_KEY) is not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        profile_repo = ProfileRepository(supabase)
        
        _profile_service_instance = ProfileService(profile_repo)
    
    return _profile_service_instance
