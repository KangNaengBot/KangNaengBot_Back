"""
ChatMessage 엔티티 - 채팅 메시지를 나타내는 도메인 객체
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ChatMessage:
    """
    채팅 메시지 엔티티
    
    Attributes:
        id: DB 내부 ID (BIGINT)
        sid: 외부 노출용 UUID
        session_id: 소속 세션 ID (ChatSession.id, BIGINT)
        role: 화자 역할 ('user', 'assistant', 'system')
        content: 메시지 내용
        created_at: 생성 시각
    """
    id: int
    sid: UUID
    session_id: int
    role: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    # Role 상수
    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_SYSTEM = 'system'
    VALID_ROLES = {ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM}
    
    @classmethod
    def create(cls, session_id: int, role: str, content: str) -> 'ChatMessage':
        """
        새 메시지 생성 (팩토리 메서드)
        
        Args:
            session_id: 세션 ID
            role: 화자 역할
            content: 메시지 내용
            
        Returns:
            ChatMessage 인스턴스
            
        Raises:
            ValueError: 유효하지 않은 role이 전달된 경우
        """
        if role not in cls.VALID_ROLES:
            raise ValueError(
                f"Invalid role: {role}. Must be one of {cls.VALID_ROLES}"
            )
        
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        
        return cls(
            id=0,  # DB 저장 후 실제 값으로 대체됨
            sid=UUID('00000000-0000-0000-0000-000000000000'),  # DB에서 생성
            session_id=session_id,
            role=role,
            content=content.strip(),
            created_at=datetime.utcnow()
        )
    
    def is_from_user(self) -> bool:
        """사용자가 보낸 메시지인지 확인"""
        return self.role == self.ROLE_USER
    
    def is_from_assistant(self) -> bool:
        """어시스턴트가 보낸 메시지인지 확인"""
        return self.role == self.ROLE_ASSISTANT
    
    def is_system_message(self) -> bool:
        """시스템 메시지인지 확인"""
        return self.role == self.ROLE_SYSTEM
