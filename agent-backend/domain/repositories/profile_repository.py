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
    
    def find_by_id(self, id: int) -> Optional[Profile]:
        """ID로 프로필 조회"""
        try:
            result = self.db.table("profiles") \
                .select("*") \
                .eq("id", id) \
                .is_("deleted_at", "null") \
                .limit(1) \
                .execute()

            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            print(f"[ProfileRepository] Error finding profile by id: {e}")
            return None

    def find_by_user_id(self, user_id: int) -> Optional[Profile]:
        """사용자 ID로 프로필 조회 (users.sid 포함)"""
        try:
            # 1. 프로필 조회
            result = self.db.table("profiles") \
                .select("*") \
                .eq("user_id", user_id) \
                .is_("deleted_at", "null") \
                .order("updated_at", desc=True) \
                .limit(1) \
                .execute()

            if not result.data or len(result.data) == 0:
                return None

            profile_data = result.data[0]

            # 2. users 테이블에서 sid 조회
            user_result = self.db.table("users") \
                .select("sid") \
                .eq("id", user_id) \
                .limit(1) \
                .execute()

            # 3. user_sid 추가
            if user_result.data and len(user_result.data) > 0:
                profile_data['user_sid'] = user_result.data[0]['sid']

            return self._to_entity(profile_data)

        except Exception as e:
            print(f"[ProfileRepository] Error finding profile by user_id: {e}")
            return None
    
    def save(self, profile: Profile) -> Profile:
        """프로필 저장 (Insert or Update)"""
        try:
            # 기존 프로필 확인 (수정된 로직으로 최신 프로필 조회)
            existing = self.find_by_user_id(profile.user_id)

            # DB에 저장할 데이터 (user_sid는 DB 컬럼이 아니므로 제외)
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

            if existing:
                # 업데이트 - 기존 ID 사용
                result = self.db.table("profiles") \
                    .update(data) \
                    .eq("id", existing.id) \
                    .execute()

                if result.data and len(result.data) > 0:
                    saved_data = result.data[0]
                    # user_sid 조회 후 추가
                    user_result = self.db.table("users") \
                        .select("sid") \
                        .eq("id", profile.user_id) \
                        .limit(1) \
                        .execute()

                    if user_result.data and len(user_result.data) > 0:
                        saved_data['user_sid'] = user_result.data[0]['sid']

                    return self._to_entity(saved_data)
            else:
                # 신규 생성
                result = self.db.table("profiles") \
                    .insert(data) \
                    .execute()

                if result.data and len(result.data) > 0:
                    saved_data = result.data[0]
                    # user_sid 조회 후 추가
                    user_result = self.db.table("users") \
                        .select("sid") \
                        .eq("id", profile.user_id) \
                        .limit(1) \
                        .execute()

                    if user_result.data and len(user_result.data) > 0:
                        saved_data['user_sid'] = user_result.data[0]['sid']

                    return self._to_entity(saved_data)

            raise Exception("Failed to save profile")

        except Exception as e:
            print(f"[ProfileRepository] Error saving profile: {e}")
            raise
    
    def _to_entity(self, row: dict) -> Profile:
        """DB Row → Entity 변환"""
        from uuid import UUID

        # user_sid 추출 (별도 조회된 경우)
        user_sid = None
        if 'user_sid' in row and row['user_sid']:
            user_sid = UUID(row['user_sid']) if isinstance(row['user_sid'], str) else row['user_sid']

        return Profile(
            id=row['id'],
            user_id=row['user_id'],
            user_sid=user_sid,
            profile_name=row['profile_name'],
            student_id=row['student_id'],
            college=row['college'],
            department=row['department'],
            major=row['major'],
            current_grade=row['current_grade'],
            current_semester=row['current_semester'],
            created_at=self._parse_datetime(row.get('created_at')),
            updated_at=self._parse_datetime(row.get('updated_at')),
            deleted_at=self._parse_datetime(row.get('deleted_at'))
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """ISO 형식 문자열을 datetime으로 변환"""
        if dt_str is None:
            return None
        if isinstance(dt_str, datetime):
            return dt_str
        if not isinstance(dt_str, str):
            print(f"[ProfileRepository] Warning: Expected str but got {type(dt_str).__name__}: {dt_str}")
            return None
        if not dt_str.strip():
            return None
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

    def delete_by_user_id(self, user_id: int) -> bool:
        """Soft Delete Profile by User ID"""
        try:
            result = self.db.table("profiles") \
                .update({
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"[ProfileRepository] Error deleting profile: {e}")
            return False

    def delete(self, id: int) -> bool:
        """Soft Delete"""
        try:
            result = self.db.table("profiles") \
                .update({
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", id) \
                .execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"[ProfileRepository] Error deleting profile: {e}")
            return False
