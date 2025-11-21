"""
ChatService - 채팅 메시지 처리 서비스

Vertex AI와 통신하고 Repository를 통해 메시지를 저장합니다.
"""
from typing import Generator, Optional
from uuid import UUID

from domain.entities.chat_message import ChatMessage
from domain.repositories.chat_message_repository import ChatMessageRepository
from domain.repositories.chat_session_repository import ChatSessionRepository
import vertexai
from vertexai import agent_engines
import config


class ChatService:
    """
    채팅 메시지 처리 서비스
    
    배포된 Vertex AI Agent Engine과 통신하여 메시지를 주고받고,
    Repository를 통해 DB에 저장합니다.
    """
    
    def __init__(
        self,
        message_repo: ChatMessageRepository,
        session_repo: ChatSessionRepository
    ):
        """
        Args:
            message_repo: ChatMessage Repository
            session_repo: ChatSession Repository
        """
        self.message_repo = message_repo
        self.session_repo = session_repo
        
        # Vertex AI 초기화
        vertexai.init(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION
        )
        
        # 배포된 Agent Engine 연결 (프로덕션 방식)
        print(f"[ChatService] Connecting to deployed Agent Engine: {config.AGENT_RESOURCE_ID}")
        self.remote_app = agent_engines.get(config.AGENT_RESOURCE_ID)
        print(f"[ChatService] ✅ Connected to: {self.remote_app.display_name or 'Agent Engine'}")
    
    def stream_message(
        self,
        user_id: int,
        session_sid: UUID,
        message_text: str
    ) -> Generator[str, None, None]:
        """
        메시지 전송 및 스트리밍 응답
        
        1. 세션 조회
        2. 사용자 메시지 저장
        3. Vertex AI에 전송 및 스트리밍 응답
        4. 에이전트 응답 저장
        5. 첫 메시지일 경우 title 자동 업데이트
        
        Args:
            user_id: 사용자 ID
            session_sid: 세션 UUID
            message_text: 사용자 메시지
            
        Yields:
            응답 텍스트 (문자 단위)
        """
        try:
            # 1. 세션 조회
            session = self.session_repo.find_by_sid(session_sid)
            if not session:
                raise ValueError(f"Session not found: {session_sid}")
            
            # user_id를 정수로 강제 변환 (타입 안전성 보장)
            user_id = int(user_id)
            
            # 세션 권한 검증
            print(f"[ChatService] Permission check: session.user_id={session.user_id}, user_id={user_id}")
            if session.user_id != user_id:
                raise PermissionError(f"Unauthorized access to session (session owner: {session.user_id}, requester: {user_id})")
            
            # 2. 사용자 메시지 저장
            user_message = ChatMessage.create(
                session_id=session.id,
                role=ChatMessage.ROLE_USER,
                content=message_text
            )
            self.message_repo.save(user_message)
            
            # 2-1. 첫 메시지인지 확인 (title이 "새로운 대화"면 첫 메시지)
            is_first_message = session.title == "새로운 대화"
            if is_first_message:
                # 메시지의 앞 50자를 title로 설정
                new_title = message_text[:50] + ("..." if len(message_text) > 50 else "")
                self.session_repo.update_title(session_sid, new_title)
                print(f"[ChatService] Updated session title: {new_title}")
            
            # 3. 배포된 Agent Engine에 메시지 전송 (스트리밍)
            full_response = ""
            
            try:
                print(f"[ChatService] Sending to deployed Agent Engine:")
                print(f"  user_id={user_id}")
                print(f"  session_id={session.vertex_session_id}")
                print(f"  message={message_text[:50]}...")
                
                # 배포된 Agent의 stream_query 메서드 호출
                for event in self.remote_app.stream_query(
                    message=message_text,
                    user_id=str(user_id),
                    session_id=session.vertex_session_id
                ):
                    # event를 문자열로 변환 (확실하게)
                    event_text = ""
                    
                    if isinstance(event, str):
                        event_text = event
                    elif isinstance(event, dict):
                        # dict인 경우 'content' 또는 'text' 키 찾기
                        event_text = str(event.get('content') or event.get('text') or event)
                    elif hasattr(event, 'content'):
                        event_text = str(event.content)
                    elif hasattr(event, 'text'):
                        event_text = str(event.text)
                    else:
                        event_text = str(event)
                    
                    # 응답 누적 (문자열로 확실히 변환 후)
                    full_response += str(event_text)
                    
                    # 문자 단위로 스트리밍
                    for char in str(event_text):
                        yield char
                
                print(f"[ChatService] Agent response complete. Total length: {len(full_response)}")
            
            except Exception as engine_error:
                error_msg = f"\n\n[Agent Engine Error] {str(engine_error)}"
                print(f"[ChatService] Agent Engine error: {engine_error}")
                import traceback
                traceback.print_exc()
                yield error_msg
                return
            
            # 4. 에이전트 응답 저장
            if full_response:
                assistant_message = ChatMessage.create(
                    session_id=session.id,
                    role=ChatMessage.ROLE_ASSISTANT,
                    content=full_response
                )
                self.message_repo.save(assistant_message)
        
        except Exception as e:
            error_msg = f"\n\n[오류] {str(e)}"
            print(f"[ChatService] Error in stream_message: {e}")
            yield error_msg
    
    def get_session_messages(
        self,
        session_sid: UUID,
        limit: Optional[int] = None
    ) -> list[ChatMessage]:
        """
        세션의 메시지 내역 조회
        
        Args:
            session_sid: 세션 UUID
            limit: 제한할 메시지 수
            
        Returns:
            메시지 목록
        """
        session = self.session_repo.find_by_sid(session_sid)
        if not session:
            return []
        
        return self.message_repo.find_by_session(session.id, limit=limit)


# Dependency Injection을 위한 싱글톤 팩토리
_chat_service_instance: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    ChatService 싱글톤 인스턴스 반환
    
    FastAPI Dependency로 사용됩니다.
    """
    global _chat_service_instance
    
    if _chat_service_instance is None:
        from supabase import create_client
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        message_repo = ChatMessageRepository(supabase)
        session_repo = ChatSessionRepository(supabase)
        _chat_service_instance = ChatService(message_repo, session_repo)
    
    return _chat_service_instance
