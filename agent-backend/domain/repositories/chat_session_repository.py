"""
ChatSession Repository 구현
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from domain.entities.chat_session import ChatSession
from domain.repositories.base import Repository
from supabase import Client


class ChatSessionRepository(Repository[ChatSession]):
    """ChatSession Repository - Supabase 구현"""
    
    def __init__(self, supabase: Client):
        """
        Args:
            supabase: Supabase 클라이언트
        """
        self.db = supabase
    
    def find_by_id(self, id: int) -> Optional[ChatSession]:
        """내부 ID(BIGINT)로 조회"""
        try:
            result = self.db.table("chat_sessions") \
                .select("*") \
                .eq("id", id) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[ChatSessionRepository] Error finding session by id: {e}")
            return None
    
    def find_by_sid(self, sid: UUID) -> Optional[ChatSession]:
        """외부 ID(UUID)로 조회"""
        try:
            result = self.db.table("chat_sessions") \
                .select("*") \
                .eq("sid", str(sid)) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[ChatSessionRepository] Error finding session by sid: {e}")
            return None
    
    def find_active_by_user(self, user_id: int) -> List[ChatSession]:
        """사용자의 활성 세션 목록 조회"""
        try:
            result = self.db.table("chat_sessions") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("is_active", True) \
                .is_("deleted_at", "null") \
                .order("created_at", desc=True) \
                .execute()
            
            return [self._to_entity(row) for row in result.data]
        except Exception as e:
            print(f"[ChatSessionRepository] Error finding active sessions: {e}")
            return []
    
    def find_all_by_user(self, user_id: int) -> List[ChatSession]:
        """사용자의 모든 세션 조회 (비활성 포함)"""
        try:
            result = self.db.table("chat_sessions") \
                .select("*") \
                .eq("user_id", user_id) \
                .is_("deleted_at", "null") \
                .order("created_at", desc=True) \
                .execute()
            
            return [self._to_entity(row) for row in result.data]
        except Exception as e:
            print(f"[ChatSessionRepository] Error finding all sessions: {e}")
            return []
    
    def save(self, session: ChatSession) -> ChatSession:
        """세션 저장 (Insert only)"""
        try:
            data = {
                "user_id": session.user_id,
                "title": session.title,
                "is_active": session.is_active,
                "vertex_session_id": session.vertex_session_id
            }
            
            result = self.db.table("chat_sessions") \
                .insert(data) \
                .execute()
            
            return self._to_entity(result.data[0])
        except Exception as e:
            print(f"[ChatSessionRepository] Error saving session: {e}")
            raise
    
    def update_active_status(self, sid: UUID, is_active: bool) -> bool:
        """활성 상태 업데이트"""
        try:
            result = self.db.table("chat_sessions") \
                .update({
                    "is_active": is_active,
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("sid", str(sid)) \
                .is_("deleted_at", "null") \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"[ChatSessionRepository] Error updating active status: {e}")
            return False
    
    def update_title(self, sid: UUID, title: str) -> bool:
        """세션 제목 업데이트"""
        try:
            result = self.db.table("chat_sessions") \
                .update({
                    "title": title,
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("sid", str(sid)) \
                .is_("deleted_at", "null") \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"[ChatSessionRepository] Error updating title: {e}")
            return False
    
    def delete(self, id: int) -> bool:
        """Soft Delete"""
        try:
            result = self.db.table("chat_sessions") \
                .update({
                    "is_active": False,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", id) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"[ChatSessionRepository] Error deleting session: {e}")
            return False

    def delete_all_by_user_id(self, user_id: int) -> bool:
        """User's All Sessions Soft Delete"""
        try:
            result = self.db.table("chat_sessions") \
                .update({
                    "is_active": False,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            return True
        except Exception as e:
            print(f"[ChatSessionRepository] Error deleting user sessions: {e}")
            return False
    
    def _to_entity(self, row: dict) -> ChatSession:
        """DB Row → Entity 변환"""
        return ChatSession(
            id=row['id'],
            sid=UUID(row['sid']),
            user_id=row['user_id'],
            title=row['title'],
            is_active=row['is_active'],
            created_at=self._parse_datetime(row['created_at']),
            updated_at=self._parse_datetime(row.get('updated_at')),
            deleted_at=self._parse_datetime(row.get('deleted_at')),
            vertex_session_id=row.get('vertex_session_id')
        )
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """ISO 형식 문자열을 datetime으로 변환"""
        if isinstance(dt_str, datetime):
            return dt_str
        # Supabase는 ISO 8601 형식 반환
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
