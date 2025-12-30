"""
ChatSession 엔티티 - 채팅 세션을 나타내는 도메인 객체
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ChatSession:
    """
    채팅 세션 엔티티
    
    Attributes:
        id: DB 내부 ID (BIGINT)
        sid: 외부 노출용 UUID
        user_id: 사용자 ID (BIGINT)
        title: 세션 제목
        is_active: 활성 상태
        created_at: 생성 시각
        vertex_session_id: Vertex AI 세션 ID
    """
    id: int
    sid: UUID
    user_id: int
    title: str
    is_active: bool
    created_at: Optional[datetime] = None
    vertex_session_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls, 
        user_id: int, 
        vertex_session_id: str,
        title: str = "새로운 대화"
    ) -> 'ChatSession':
        """
        새 세션 생성 (팩토리 메서드)
        
        DB 저장 전 객체를 생성합니다.
        id와 sid는 DB에서 자동으로 생성되므로 임시값을 사용합니다.
        
        Args:
            user_id: 사용자 ID
            vertex_session_id: Vertex AI 세션 ID
            title: 세션 제목
            
        Returns:
            ChatSession 인스턴스
        """
        return cls(
            id=0,  # DB 저장 후 실제 값으로 대체됨
            sid=UUID('00000000-0000-0000-0000-000000000000'),  # DB에서 생성
            user_id=user_id,
            title=title,
            is_active=True,
            created_at=datetime.utcnow(),
            vertex_session_id=vertex_session_id
        )
    
    def deactivate(self) -> None:
        """세션 비활성화 (소프트 삭제)"""
        self.is_active = False
    
    def update_title(self, new_title: str) -> None:
        """세션 제목 변경"""
        if not new_title or not new_title.strip():
            raise ValueError("Title cannot be empty")
        self.title = new_title.strip()
