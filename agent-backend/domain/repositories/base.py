"""
기본 Repository 추상 클래스
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Repository 기본 인터페이스
    
    모든 Repository는 이 인터페이스를 구현해야 합니다.
    """
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        """
        ID로 엔티티 조회
        
        Args:
            id: 엔티티 ID (BIGINT)
            
        Returns:
            엔티티 또는 None
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        엔티티 저장 (Insert)
        
        Args:
            entity: 저장할 엔티티
            
        Returns:
            저장된 엔티티 (DB에서 생성된 ID 포함)
        """
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        엔티티 삭제 (Hard Delete)
        
        Args:
            id: 삭제할 엔티티 ID
            
        Returns:
            삭제 성공 여부
        """
        pass
