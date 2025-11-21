"""
메모리 관리 서비스 - Vertex AI Agent Engine Memory Bank 연동
"""
from typing import List, Dict, Optional
import vertexai
from vertexai import agent_engines
import config

class MemoryManager:
    """
    Vertex AI Agent Engine Memory Bank 관리자
    
    Agent Engine은 세션 내의 대화를 바탕으로 자동으로 메모리를 관리할 수 있습니다.
    이 클래스는 명시적으로 메모리를 조회하거나 생성할 때 사용됩니다.
    """
    
    def __init__(self):
        """Agent Engine 초기화"""
        self.engine = agent_engines.get(config.AGENT_RESOURCE_ID)

    def get_memory(self, user_id: str) -> str:
        """
        사용자의 기억(Memory) 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            memory_content: 요약된 기억 내용 (텍스트)
        """
        try:
            # Vertex AI Agent Engine에서 사용자의 메모리를 조회
            # filter를 사용하여 특정 사용자의 메모리만 가져옴
            memories = self.engine.list_memories(filter=f"user_id={user_id}")
            
            # 메모리 객체에서 텍스트 추출 (구조에 따라 조정 필요)
            # 보통 memory.content 또는 memory.text 속성을 가짐
            memory_texts = []
            for memory in memories:
                if hasattr(memory, 'content'):
                    memory_texts.append(memory.content)
                elif hasattr(memory, 'text'):
                    memory_texts.append(memory.text)
                else:
                    # 객체 구조를 모를 경우 문자열로 변환
                    memory_texts.append(str(memory))
            
            return "\n\n".join(memory_texts)
            
        except Exception as e:
            print(f"[MemoryManager] Failed to get memory: {e}")
            return ""

    def create_memory(self, user_id: str, text: str):
        """
        명시적으로 메모리 생성 (중요 정보 저장)
        
        Args:
            user_id: 사용자 ID
            text: 저장할 내용
        """
        try:
            # Vertex AI Agent Engine에 메모리 주입
            # create_memory 메서드 사용 (메서드명 확인 필요)
            self.engine.create_memory(
                user_id=user_id,
                content=text
            )
            print(f"[MemoryManager] Memory created for {user_id}")
            
        except Exception as e:
            print(f"[MemoryManager] Failed to create memory: {e}")

    def retrieve_context(self, user_id: str, query: str) -> str:
        """
        현재 대화와 관련된 컨텍스트 검색 (RAG)
        """
        # Memory Bank가 자동으로 작동한다면 이 메서드는 필요 없을 수 있음.
        # 하지만 명시적 검색이 필요하다면 구현.
        return self.get_memory(user_id)

# 싱글톤 인스턴스
_memory_manager_instance = None

def get_memory_manager() -> MemoryManager:
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance
