"""
ChatMessage Repository 구현
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from domain.entities.chat_message import ChatMessage
from domain.repositories.base import Repository
from supabase import Client


class ChatMessageRepository(Repository[ChatMessage]):
    """ChatMessage Repository - Supabase 구현"""
    
    def __init__(self, supabase: Client):
        """
        Args:
            supabase: Supabase 클라이언트
        """
        self.db = supabase
    
    def find_by_id(self, id: int) -> Optional[ChatMessage]:
        """내부 ID(BIGINT)로 조회"""
        try:
            result = self.db.table("chat_messages") \
                .select("*") \
                .eq("id", id) \
                .is_("deleted_at", "null") \
                .single() \
                .execute()
            
            if result.data:
                return self._to_entity(result.data)
            return None
        except Exception as e:
            print(f"[ChatMessageRepository] Error finding message by id: {e}")
            return None
    
    def find_by_session(self, session_id: int, limit: Optional[int] = None) -> List[ChatMessage]:
        """
        세션 ID로 메시지 조회
        
        Args:
            session_id: 세션 내부 ID (BIGINT)
            limit: 제한할 메시지 수 (None이면 전체)
            
        Returns:
            메시지 목록 (시간순 정렬)
        """
        try:
            query = self.db.table("chat_messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .is_("deleted_at", "null") \
                .order("created_at")
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return [self._to_entity(row) for row in result.data]
        except Exception as e:
            print(f"[ChatMessageRepository] Error finding messages by session: {e}")
            return []
    
    def find_recent_by_session(self, session_id: int, count: int = 10) -> List[ChatMessage]:
        """최근 N개 메시지 조회"""
        try:
            result = self.db.table("chat_messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .is_("deleted_at", "null") \
                .order("created_at", desc=True) \
                .limit(count) \
                .execute()
            
            # 시간순 정렬로 되돌리기
            messages = [self._to_entity(row) for row in result.data]
            return list(reversed(messages))
        except Exception as e:
            print(f"[ChatMessageRepository] Error finding recent messages: {e}")
            return []
    
    def save(self, message: ChatMessage) -> ChatMessage:
        """메시지 저장 (Insert only)"""
        try:
            data = {
                "session_id": message.session_id,
                "role": message.role,
                "content": message.content
            }
            
            result = self.db.table("chat_messages") \
                .insert(data) \
                .execute()
            
            return self._to_entity(result.data[0])
        except Exception as e:
            print(f"[ChatMessageRepository] Error saving message: {e}")
            raise
    
    def delete(self, id: int) -> bool:
        """Soft Delete"""
        try:
            result = self.db.table("chat_messages") \
                .update({
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", id) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"[ChatMessageRepository] Error deleting message: {e}")
            return False
    
    def delete_by_session(self, session_id: int) -> bool:
        """세션의 모든 메시지 Soft Delete"""
        try:
            result = self.db.table("chat_messages") \
                .update({
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("session_id", session_id) \
                .execute()
            
            return True
        except Exception as e:
            print(f"[ChatMessageRepository] Error deleting messages by session: {e}")
            return False

    def delete_by_session_ids(self, session_ids: List[int]) -> bool:
        """여러 세션의 모든 메시지 Soft Delete"""
        if not session_ids:
            return True
            
        try:
            result = self.db.table("chat_messages") \
                .update({
                    "deleted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .in_("session_id", session_ids) \
                .execute()
            return True
        except Exception as e:
            print(f"[ChatMessageRepository] Error deleting messages by session ids: {e}")
            return False
    
    def _to_entity(self, row: dict) -> ChatMessage:
        """DB Row → Entity 변환"""
        return ChatMessage(
            id=row['id'],
            sid=UUID(row['sid']),
            session_id=row['session_id'],
            role=row['role'],
            content=row['content'],
            created_at=self._parse_datetime(row['created_at']),
            updated_at=self._parse_datetime(row.get('updated_at')),
            deleted_at=self._parse_datetime(row.get('deleted_at'))
        )
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """ISO 형식 문자열을 datetime으로 변환"""
        if isinstance(dt_str, datetime):
            return dt_str
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
