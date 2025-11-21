"""
User 엔티티 - 사용자를 나타내는 도메인 객체
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class User:
    """
    사용자 엔티티
    
    Attributes:
        id: DB 내부 ID (BIGINT)
        sid: 외부 노출용 UUID
        google_id: Google OAuth ID
        email: 이메일 주소
        name: 사용자 이름
        created_at: 생성 시각
        updated_at: 수정 시각
    """
    id: int
    sid: UUID
    google_id: str
    email: str
    name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def create(
        cls,
        google_id: str,
        email: str,
        name: Optional[str] = None
    ) -> 'User':
        """
        새 사용자 생성 (팩토리 메서드)
        
        Args:
            google_id: Google OAuth ID
            email: 이메일 주소
            name: 사용자 이름 (선택)
            
        Returns:
            User 인스턴스
        """
        now = datetime.utcnow()
        return cls(
            id=0,  # DB 저장 후 실제 값으로 대체됨
            sid=UUID('00000000-0000-0000-0000-000000000000'),  # DB에서 생성
            google_id=google_id,
            email=email,
            name=name,
            created_at=now,
            updated_at=now
        )
    
    def update_name(self, new_name: str) -> None:
        """사용자 이름 변경"""
        self.name = new_name
        self.updated_at = datetime.utcnow()
    
    def update_email(self, new_email: str) -> None:
        """이메일 주소 변경"""
        if not new_email or '@' not in new_email:
            raise ValueError("Invalid email address")
        self.email = new_email
        self.updated_at = datetime.utcnow()
