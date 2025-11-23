"""
Profile Repository 구현
"""
from typing import Optional
from datetime import datetime

from domain.entities.profile import Profile
from domain.repositories.base import Repository
from supabase import Client


class ProfileRepository(Repository[Profile]):
    """Profile Repository - Supabase 구현"""
    
    def __init__(self, supabase: Client):
        """
        Args:
            supabase: Supabase 클라이언트
        """
        self.db = supabase
    
    def find_by_user_id(self, user_id: int) -> Optional[Profile]:
        """사용자 ID로 프로필 조회"""
        try:
            result = self.db.table("profiles") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            # 데이터가 없는 경우도 에러로 처리될 수 있음 (Supabase 특성)
            # print(f"[ProfileRepository] Error finding profile by user_id: {e}")
            return None
    
    def save(self, profile: Profile) -> Profile:
        """프로필 저장 (Insert or Update)"""
        try:
            data = {
                "user_id": profile.user_id,
                "profile_name": profile.profile_name,
                "student_id": profile.student_id,
                "college": profile.college,
                "department": profile.department,
                "major": profile.major,
                "current_grade": profile.current_grade,
                "current_semester": profile.current_semester
            }
            
            # upsert 사용 (user_id가 unique constraint여야 함)
            result = self.db.table("profiles") \
                .upsert(data, on_conflict="user_id") \
                .select("*") \
                .execute()
            
            if result.data:
                return self._to_entity(result.data[0])
            raise Exception("Failed to save profile")
            
        except Exception as e:
            print(f"[ProfileRepository] Error saving profile: {e}")
            raise
    
    def _to_entity(self, row: dict) -> Profile:
        """DB Row → Entity 변환"""
        return Profile(
            id=row['id'],
            user_id=row['user_id'],
            profile_name=row['profile_name'],
            student_id=row['student_id'],
            college=row['college'],
            department=row['department'],
            major=row['major'],
            current_grade=row['current_grade'],
            current_semester=row['current_semester'],
            created_at=self._parse_datetime(row.get('created_at')),
            updated_at=self._parse_datetime(row.get('updated_at'))
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """ISO 형식 문자열을 datetime으로 변환"""
        if not dt_str:
            return None
        if isinstance(dt_str, datetime):
            return dt_str
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

    # Repository 추상 메서드 구현 (필요 없으면 pass)
    def find_by_id(self, id: int) -> Optional[Profile]:
        pass
        
    def delete(self, id: int) -> bool:
        pass
