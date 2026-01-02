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
from utils.input_sanitizer import sanitize_message
import vertexai
import config
import asyncio


class ChatService:
    """
    채팅 메시지 처리 서비스

    배포된 Vertex AI Agent Engine과 통신하여 메시지를 주고받고,
    Repository를 통해 DB에 저장합니다.
    """

    # 게스트 사용자 ID 범위 (dependencies.py와 동일)
    GUEST_ID_MIN = 100000000
    GUEST_ID_MAX = 999999999

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
        
        # ✅ 신규 Client-based API 사용 (공식 문서 권장)
        # https://cloud.google.com/python/docs/reference/aiplatform/latest
        self.client = vertexai.Client(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION
        )
        
        print(f"[ChatService] ✅ Vertex AI Client initialized: {config.GOOGLE_CLOUD_PROJECT}/{config.VERTEX_AI_LOCATION}")

        # 배포된 Agent Engine 연결
        resource_id = config.AGENT_RESOURCE_ID.strip()

        # Full resource name을 숫자 ID로 변환 (필요시)
        if resource_id.startswith("projects/"):
            # 이미 full resource name 형식
            print(f"[ChatService] Using full resource name: {resource_id}")
        else:
            # 숫자 ID만 있는 경우 full resource name 생성
            resource_id = f"projects/{config.GOOGLE_CLOUD_PROJECT}/locations/{config.VERTEX_AI_LOCATION}/reasoningEngines/{resource_id}"
            print(f"[ChatService] Constructed full resource name: {resource_id}")

        print(f"[ChatService] Connecting to deployed Agent Engine...")
        
        # 신규 API로 Agent Engine 가져오기
        self.remote_app = self.client.agent_engines.get(name=resource_id)
        print(f"[ChatService] ✅ Connected to Agent Engine: {resource_id}")
        print(f"[ChatService] 🔍 Remote app type: {type(self.remote_app).__name__}")
    
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
            # ========================================
            # 🛡️ 보안: 입력 살균 (최우선 처리)
            # ========================================
            # 서비스 레이어 진입 시 가장 먼저 실행
            # XSS, Script Injection, HTML 태그 등 제거
            message_text = sanitize_message(message_text)
            
            if not message_text:
                raise ValueError("Message cannot be empty after sanitization")
            
            print(f"[ChatService] ✅ Input sanitized (length: {len(message_text)})")
            # ========================================
            
            # 1. 세션 조회
            session = self.session_repo.find_by_sid(session_sid)
            if not session:
                raise ValueError(f"Session not found: {session_sid}")

            # 1-1. Vertex AI 세션 존재 여부 확인
            print(f"[ChatService] 🔍 Verifying Vertex AI session exists...")
            from services.session_service import get_session_service
            session_service = get_session_service()

            vertex_session = await session_service.get_vertex_session(
                user_id=session.user_id,
                session_id=session.vertex_session_id
            )

            if not vertex_session:
                error_msg = f"❌ Vertex AI session not found or expired: {session.vertex_session_id}"
                print(f"[ChatService] {error_msg}")
                print(f"[ChatService] Creating new Vertex AI session to recover...")

                # 새 Vertex AI 세션 생성 및 DB 업데이트
                try:
                    new_session = await session_service.create_session(
                        user_id=session.user_id,
                        title=session.title
                    )
                    # 기존 세션의 vertex_session_id를 새로운 것으로 교체
                    # Note: 이전 대화 내역은 유지되나, Vertex AI 컨텍스트는 새로 시작됨
                    print(f"[ChatService] ✅ Created new Vertex AI session: {new_session.vertex_session_id}")
                    print(f"[ChatService] ⚠️ Warning: Previous conversation context in Vertex AI is lost")
                    session.vertex_session_id = new_session.vertex_session_id
                except Exception as recovery_error:
                    raise ValueError(f"Failed to recover session: {str(recovery_error)}")

            # user_id를 정수로 강제 변환 (타입 안전성 보장)
            user_id = int(user_id)

            # 세션 권한 검증
            print(f"[ChatService] Permission check: session.user_id={session.user_id}, user_id={user_id}")
            if session.user_id != user_id:
                # 게스트 세션인 경우 권한 검증 완화 (누구나 접근 가능)
                is_guest_session = self.GUEST_ID_MIN <= session.user_id <= self.GUEST_ID_MAX

                if is_guest_session:
                    print(f"[ChatService] ✅ Guest session access allowed: session_owner={session.user_id}, requester={user_id}")
                else:
                    # 일반 사용자 세션은 엄격하게 검증
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
            # 빈 응답인 경우 재시도 (최대 3회), Exception 발생 시 즉시 중단
            max_retries = 3
            full_response = ""
            
            for attempt in range(max_retries):
                try:
                    full_response = ""
                    
                    print(f"[ChatService] Sending to deployed Agent Engine (Attempt {attempt+1}/{max_retries}):")
                    print(f"  user_id={user_id}")
                    print(f"  session_id={session.vertex_session_id}")
                    # print(f"  message={message_text[:50]}...")
                    
                    # 배포된 Agent의 stream_query 메서드 호출
                    print(f"[ChatService] 📤 Message preview: {enhanced_message[:200]}...")
                    print(f"[ChatService] 📤 Parameters:")
                    print(f"    message length: {len(enhanced_message)}")
                    print(f"    user_id: {user_id} (type: {type(user_id).__name__})")
                    print(f"    session_id: {session.vertex_session_id} (type: {type(session.vertex_session_id).__name__})")

                    # 디버깅: 간단한 메시지로 테스트
                    test_message = "Hello" if attempt == max_retries - 1 and not full_response else enhanced_message
                    if test_message != enhanced_message:
                        print(f"[ChatService] 🧪 Testing with simple message: '{test_message}'")

                    # ⚠️ 중요: ADK는 세션 소유자의 user_id를 사용해야 함
                    # 게스트 모드에서 다른 user_id로 접근해도, 세션 소유자의 ID로 쿼리해야 함
                    session_owner_id = str(session.user_id)

                    print(f"[ChatService] 🔑 Using session owner's user_id for ADK: {session_owner_id}")
                    print(f"[ChatService] 🔑 Session details:")
                    print(f"    - DB session.id: {session.id}")
                    print(f"    - DB session.sid: {session.sid}")
                    print(f"    - Vertex session_id: {session.vertex_session_id}")
                    print(f"    - Session created_at: {session.created_at}")

                    # ⚠️ 디버깅: stream_query 호출 직전 파라미터 확인
                    print(f"[ChatService] 🚀 Calling remote_app.stream_query with:")
                    print(f"    - remote_app type: {type(self.remote_app).__name__}")
                    print(f"    - remote_app resource_name: {getattr(self.remote_app, 'resource_name', 'N/A')}")
                    print(f"    - message: '{test_message}' (type: {type(test_message).__name__})")
                    print(f"    - user_id: '{session_owner_id}' (type: {type(session_owner_id).__name__})")
                    print(f"    - session_id: '{session.vertex_session_id}' (type: {type(session.vertex_session_id).__name__})")

                    # ✅ 공식 문서에 따른 올바른 쿼리 방법
                    # async for event in remote_app.async_stream_query(
                    #     user_id="user-id",
                    #     message="What is the exchange rate...",
                    # ):
                    print(f"[ChatService] � Calling remote_app.async_stream_query()")
                    
                    # 비동기 스트림 쿼리 (공식 API)
                    async for event in self.remote_app.async_stream_query(
                        user_id=session_owner_id,
                        message=test_message,
                    ):
                        print(f"[ChatService] 📥 Event received: {type(event).__name__}")
                        print(f"[ChatService] 📥 Event: {event}")
                        
                        # 이벤트에서 텍스트 추출
                        event_text = self._extract_text_from_event(event)
                        
                        if not event_text:
                            print(f"[ChatService] ⚠️ No text extracted from event")
                            continue
                        
                        full_response += event_text
                        yield event_text
                    
                    if not full_response:
                        if attempt < max_retries - 1:
                            print(f"[ChatService] Empty response. Retrying in 2 seconds ... ({attempt+1}/{max_retries})")
                            await asyncio.sleep(2)
                            continue
                        else:
                            print(f"[ChatService] ⚠️ Empty response after {max_retries} streaming attempts.")
                            print(f"[ChatService] 💡 Possible causes:")
                            print(f"    - Vertex AI session may be invalid or expired")
                            print(f"    - Agent Engine internal error")
                            print(f"    - Network timeout or rate limiting")
                            print(f"    - Message format issue")
                    else:
                        # 성공 시 루프 종료
                        break
                
                except Exception as engine_error:
                    # 사용자 요청: Exception 발생 시 재시도 하지 않고 에러 메시지 전송
                    error_msg = f"\n\n[System Error] 응답 생성에 실패했습니다. (Error Code: 500, Details: {str(engine_error)})"
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
    
    def _extract_text_from_event(self, event) -> str:
        """
        Vertex AI 응답 이벤트에서 텍스트 추출
        다양한 응답 구조(Dict, Object)를 유연하게 처리
        """
        text = ""
        try:
            # 1. Dictionary 구조 처리
            if isinstance(event, dict):
                # 1-1. content.parts 구조 (User Provided Log Case)
                # {'content': {'parts': [{'text': '...'}], 'role': 'model'}}
                if 'content' in event and isinstance(event['content'], dict):
                    parts = event['content'].get('parts', [])
                    for part in parts:
                        if isinstance(part, dict):
                            text += part.get('text', '')
                        elif hasattr(part, 'text'):
                            text += part.text
                            
                # 1-2. parts 직접 접근
                elif 'parts' in event:
                    parts = event['parts']
                    for part in parts:
                        if isinstance(part, dict):
                            text += part.get('text', '')
                        elif hasattr(part, 'text'):
                            text += part.text

                # 1-3. 단순 텍스트 필드
                elif 'text' in event:
                    text = str(event['text'])
                elif 'content' in event and isinstance(event['content'], str):
                    text = str(event['content'])
            
            # 2. Object 구조 처리 (SDK Response Objects)
            else:
                if hasattr(event, 'parts'):
                    for part in event.parts:
                        if hasattr(part, 'text'):
                            text += part.text
                elif hasattr(event, 'text'):
                    text = str(event.text)
                elif hasattr(event, 'content'):
                    text = str(event.content)
                elif isinstance(event, str):
                    text = event
                    
        except Exception as e:
            # 파싱 에러는 로그만 남기고 무시 (스트림 중단 방지)
            print(f"[ChatService] Failed to parse event: {e}, Event: {event}")
            
        return text

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

