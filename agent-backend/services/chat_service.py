"""
ChatService - 채팅 메시지 처리 서비스

Vertex AI와 통신하고 Repository를 통해 메시지를 저장합니다.
"""
from typing import AsyncGenerator, Optional
from uuid import UUID

from domain.entities.chat_message import ChatMessage
from domain.repositories.chat_message_repository import ChatMessageRepository
from domain.repositories.chat_session_repository import ChatSessionRepository
from domain.repositories.profile_repository import ProfileRepository
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
        session_repo: ChatSessionRepository,
        profile_repo: ProfileRepository
    ):
        """
        Args:
            message_repo: ChatMessage Repository
            session_repo: ChatSession Repository
            profile_repo: Profile Repository
        """
        self.message_repo = message_repo
        self.session_repo = session_repo
        self.profile_repo = profile_repo
        
        # Vertex AI 초기화
        vertexai.init(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION
        )
        
        # 배포된 Agent Engine 연결 (프로덕션 방식)
        print(f"[ChatService] Connecting to deployed Agent Engine: {config.AGENT_RESOURCE_ID}")
        self.remote_app = agent_engines.get(config.AGENT_RESOURCE_ID)
        print(f"[ChatService] ✅ Connected to: {self.remote_app.display_name or 'Agent Engine'}")
    
    async def stream_message(
        self,
        user_id: int,
        session_sid: UUID,
        message_text: str
    ) -> AsyncGenerator[str, None]:
        """
        메시지 전송 및 스트리밍 응답 (비동기)
        
        1. 세션 조회
        2. 사용자 메시지 저장
        3. 프로필 정보 조회 및 주입
        4. Vertex AI에 전송 및 스트리밍 응답
        5. 에이전트 응답 저장
        6. 첫 메시지일 경우 title 자동 업데이트
        
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
            
            # 2. 최근 대화 내역 조회 (현재 메시지 저장 전)
            try:
                # 최근 10개 메시지 조회 (현재 메시지는 아직 저장 안 됨)
                recent_messages = self.message_repo.find_recent_by_session(session.id, count=10)
                
                history_context = ""
                if recent_messages:
                    history_context = "[이전 대화 내역]\n"
                    for msg in recent_messages:
                        role_name = "User" if msg.role == "user" else "Assistant"
                        # 메시지 내용이 너무 길면 자르기 (선택 사항)
                        content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                        history_context += f"{role_name}: {content}\n"
                    history_context += "---\n"
                    print(f"[ChatService] Loaded {len(recent_messages)} recent messages for context")
            except Exception as e:
                print(f"[ChatService] Failed to load chat history: {e}")
                history_context = ""

            # 3. 사용자 메시지 저장
            user_message = ChatMessage.create(
                session_id=session.id,
                role=ChatMessage.ROLE_USER,
                content=message_text
            )
            self.message_repo.save(user_message)
            
            # 3-1. 첫 메시지인지 확인 (title이 "새로운 대화"면 첫 메시지)
            is_first_message = session.title == "새로운 대화"
            if is_first_message:
                # 메시지의 앞 50자를 title로 설정
                new_title = message_text[:50] + ("..." if len(message_text) > 50 else "")
                self.session_repo.update_title(session_sid, new_title)
                print(f"[ChatService] Updated session title: {new_title}")
            
            # 3-2. 사용자 프로필 정보 조회 (있으면 컨텍스트로 추가)
            try:
                # Repository를 통해 동기적으로 조회
                profile_context = self._get_profile_context(user_id)
            except Exception as e:
                print(f"[ChatService] Failed to get profile context: {e}")
                profile_context = ""
            
            # 3-3. 컨텍스트 조합 (프로필 + 히스토리 + 현재 메시지)
            enhanced_message = message_text
            
            # 컨텍스트가 있으면 주입
            if profile_context or history_context:
                context_parts = []
                if profile_context:
                    context_parts.append(profile_context)
                if history_context:
                    context_parts.append(history_context)
                
                # 컨텍스트와 현재 메시지 결합
                enhanced_message = f"{''.join(context_parts)}\n[현재 질문]\n{message_text}"
                
                if profile_context:
                    print(f"[ChatService] Profile context added for user {user_id}")
            
            # 3. 배포된 Agent Engine에 메시지 전송 (스트리밍)
            full_response = ""
            
            try:
                print(f"[ChatService] Sending to deployed Agent Engine:")
                print(f"  user_id={user_id}")
                print(f"  session_id={session.vertex_session_id}")
                print(f"  message={message_text[:50]}...")
                
                # 배포된 Agent의 stream_query 메서드 호출 (프로필 정보 포함)
                for event in self.remote_app.stream_query(
                    message=enhanced_message,  # 프로필 정보가 포함된 메시지
                    user_id=str(user_id),
                    session_id=session.vertex_session_id
                ):
                    # event를 문자열로 변환
                    event_text = ""
                    
                    # 1. parts 속성/키 확인 (Vertex AI 표준 응답 구조)
                    parts_list = None
                    
                    # 1-1. 객체의 parts 속성
                    if hasattr(event, 'parts') and event.parts:
                        parts_list = event.parts
                    # 1-2. dict의 content.parts 구조 (실제 Vertex AI 응답)
                    elif isinstance(event, dict) and 'content' in event and isinstance(event['content'], dict):
                        if 'parts' in event['content']:
                            parts_list = event['content']['parts']
                    # 1-3. dict의 직접 parts 키
                    elif isinstance(event, dict) and 'parts' in event:
                        parts_list = event['parts']
                    
                    if parts_list:
                        for part in parts_list:
                            # 딕셔너리 형태의 part 처리
                            if isinstance(part, dict):
                                # 함수 호출/응답은 건너뛰기
                                if 'function_call' in part or 'function_response' in part:
                                    continue
                                if 'text' in part:
                                    event_text += part['text']
                            # 객체 형태의 part 처리
                            else:
                                if hasattr(part, 'function_call') and part.function_call:
                                    continue
                                if hasattr(part, 'function_response') and part.function_response:
                                    continue
                                if hasattr(part, 'text') and part.text:
                                    event_text += part.text
                    
                    # 2. 문자열인 경우
                    elif isinstance(event, str):
                        event_text = event
                        
                    # 3. 딕셔너리에서 직접 text/content 추출
                    elif isinstance(event, dict):
                        # 함수 호출/응답 데이터는 무시
                        if 'function_call' in event or 'function_response' in event:
                            continue
                            
                        # text나 content 키가 있는 경우만 추출
                        if 'text' in event:
                            event_text = str(event['text'])
                        elif 'content' in event:
                            event_text = str(event['content'])
                        
                    # 4. 기타 속성 확인
                    elif hasattr(event, 'text') and event.text:
                        event_text = str(event.text)
                    elif hasattr(event, 'content') and event.content:
                        event_text = str(event.content)
                    
                    # 텍스트가 없으면 건너뛰기
                    if not event_text:
                        continue
                    
                    # 응답 누적
                    full_response += event_text
                    
                    # 문자 단위로 스트리밍
                    for char in event_text:
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
                
                # 5. 메모리 생성 트리거 (비동기) - 현재 SDK 버전에서 미지원으로 주석 처리
                # 대화가 끝난 후, 이번 턴의 내용을 Memory Bank에 보내서 기억할 내용이 있는지 분석하게 함
                # try:
                #     from vertexai.preview import reasoning_engines
                #     
                #     # 이번 턴의 대화 내용 (User + Assistant)
                #     events = [
                #         {"content": {"role": "user", "parts": [{"text": message_text}]}},
                #         {"content": {"role": "model", "parts": [{"text": full_response}]}}
                #     ]
                #     
                #     print(f"[ChatService] Triggering memory generation for user {user_id}...")
                #     
                #     # 비동기로 메모리 생성 요청 (wait_for_completion=False)
                #     reasoning_engines.ReasoningEngine.generate_memories(
                #         resource_name=self.remote_app.resource_name,
                #         direct_contents_source={"events": events},
                #         scope={"user_id": str(user_id)},
                #         config={"wait_for_completion": False}
                #     )
                #     print(f"[ChatService] ✅ Memory generation triggered (Background)")
                #     
                # except Exception as mem_error:
                #     # 메모리 생성 실패가 채팅 응답에 영향을 주면 안 됨
                #     print(f"[ChatService] ⚠️ Failed to trigger memory generation: {mem_error}")
        
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
    
    def _get_profile_context(self, user_id: int) -> str:
        """
        사용자 프로필 정보를 조회하여 컨텍스트 문자열로 반환
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            프로필 컨텍스트 문자열 (없으면 빈 문자열)
        """
        try:
            profile = self.profile_repo.find_by_user_id(user_id)
            
            if not profile:
                return ""
            
            # 프로필 정보를 구조화된 컨텍스트로 변환
            context = f"""[사용자 프로필 정보]
이름: {profile.profile_name}
학번: {profile.student_id}
단과대학: {profile.college}
학과: {profile.department}
전공: {profile.major}
현재 학년: {profile.current_grade}학년
현재 학기: {profile.current_semester}학기
---
위 정보를 바탕으로 사용자에게 맞춤형 답변을 제공해주세요.
"""
            return context
                
        except Exception as e:
            print(f"[ChatService] Failed to fetch profile for user {user_id}: {e}")
            return ""  # 프로필 조회 실패 시 빈 문자열 반환 (서비스는 계속 진행)


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
        from urllib.parse import urlparse
        
        # DATABASE_URL에서 Supabase URL 추출
        db_url = config.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL is not configured")
        
        parsed = urlparse(db_url)
        username = parsed.username
        
        if username and '.' in username:
            project_ref = username.split('.', 1)[1]
            supabase_url = f"https://{project_ref}.supabase.co"
        else:
            raise ValueError("Invalid DATABASE_URL format: cannot extract project_ref")
        
        # API 키는 config에서 가져오기
        supabase_key = config.SUPABASE_KEY
        if not supabase_key:
            raise ValueError("SUPABASE_KEY (DATABASE_KEY) is not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        message_repo = ChatMessageRepository(supabase)
        session_repo = ChatSessionRepository(supabase)
        profile_repo = ProfileRepository(supabase)
        
        _chat_service_instance = ChatService(
            message_repo, 
            session_repo,
            profile_repo
        )
    
    return _chat_service_instance

