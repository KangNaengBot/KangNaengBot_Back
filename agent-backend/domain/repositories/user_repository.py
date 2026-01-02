"""
User Repository 구현
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from domain.entities.user import User
from domain.repositories.base import Repository
from supabase import Client


class UserRepository(Repository[User]):
    """User Repository - Supabase 구현"""
    
    def __init__(self, supabase: Client):
        """
        Args:
            supabase: Supabase 클라이언트
        """
        self.db = supabase
    
    def find_by_id(self, id: int) -> Optional[User]:
        """내부 ID(BIGINT)로 조회"""
        try:
            result = self.db.table("users") \
                .select("*") \
                .eq("id", id) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[UserRepository] Error finding user by id: {e}")
            return None
    
    def find_by_sid(self, sid: UUID) -> Optional[User]:
        """외부 ID(UUID)로 조회"""
        try:
            result = self.db.table("users") \
                .select("*") \
                .eq("sid", str(sid)) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[UserRepository] Error finding user by sid: {e}")
            return None
    
    def find_by_google_id(self, google_id: str) -> Optional[User]:
        """Google ID로 조회"""
        try:
            result = self.db.table("users") \
                .select("*") \
                .eq("google_id", google_id) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[UserRepository] Error finding user by google_id: {e}")
            return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """이메일로 조회"""
        try:
            result = self.db.table("users") \
                .select("*") \
                .eq("email", email) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[UserRepository] Error finding user by email: {e}")
            return None
    
    def save(self, user: User) -> User:
        """사용자 저장 (Insert only)"""
        try:
            data = {
                "google_id": user.google_id,
                "email": user.email,
                "name": user.name
            }
            
            result = self.db.table("users") \
                .insert(data) \
                .select("*") \
                .execute()
            
            return self._to_entity(result.data[0])
        except Exception as e:
            print(f"[UserRepository] Error saving user: {e}")
            raise
    
    def update(self, user: User) -> bool:
        """사용자 정보 업데이트"""
        try:
            data = {
                "email": user.email,
                "name": user.name,
                "updated_at": user.updated_at.isoformat()
            }
            
            result = self.db.table("users") \
                .update(data) \
                .eq("id", user.id) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"[UserRepository] Error updating user: {e}")
            return False
    
    def delete(self, id: int) -> bool:
        """Soft Delete"""
        try:
            result = self.db.table("users") \
                .update({"deleted_at": datetime.utcnow().isoformat()}) \
                .eq("id", id) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"[UserRepository] Error deleting user: {e}")
            return False
    
    def _to_entity(self, row: dict) -> User:
        """DB Row → Entity 변환"""
        return User(
            id=row['id'],
            sid=UUID(row['sid']),
            google_id=row['google_id'],
            email=row['email'],
            name=row.get('name'),
            created_at=self._parse_datetime(row['created_at']),
            updated_at=self._parse_datetime(row['updated_at']),
            deleted_at=self._parse_datetime(row['deleted_at']) if row.get('deleted_at') else None
        )
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """ISO 형식 문자열을 datetime으로 변환"""
        if dt_str is None:
            return None
        if isinstance(dt_str, datetime):
            return dt_str
        if not isinstance(dt_str, str):
            print(f"[UserRepository] Warning: Expected str but got {type(dt_str).__name__}: {dt_str}")
            return None
        if not dt_str.strip():
            return None
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
