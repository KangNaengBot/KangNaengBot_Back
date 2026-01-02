"""
SessionService - ADK VertexAiSessionService를 사용한 세션 관리

Agent Engine이 실제 세션을 관리하고, DB에는 메타데이터만 저장합니다.
"""
from typing import Optional, List
from uuid import UUID
import asyncio

from google.adk.sessions import VertexAiSessionService
from domain.entities.chat_session import ChatSession
from domain.repositories.chat_session_repository import ChatSessionRepository
import config


class SessionService:
    """
    세션 관리 서비스
    
    - Vertex AI Session Service: 실제 대화 내용 및 상태 관리
    - Supabase DB: UI에 표시할 메타데이터 저장 (title, created_at 등)
    """
    
    def __init__(self, session_repo: ChatSessionRepository):
        """
        Args:
            session_repo: ChatSession Repository
        """
        self.repo = session_repo
        
        # Vertex AI Session Service 초기화
        self.vertex_session_service = VertexAiSessionService(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION
        )
        
        # Agent Engine ID (app_name으로 사용)
        # 중요: 값 뒤에 개행 문자(\n)가 포함될 수 있으므로 반드시 strip() 처리
        self.app_name = config.AGENT_RESOURCE_ID.strip() if config.AGENT_RESOURCE_ID else None
    
    async def create_session(self, user_id: int, title: str = "새로운 대화") -> ChatSession:
        """
        새 세션 생성

        1. Vertex AI Session Service에서 세션 생성
        2. DB에 메타데이터 저장

        Args:
            user_id: 사용자 ID (BIGINT)
            title: 세션 제목

        Returns:
            생성된 ChatSession 엔티티
        """
        try:
            # 1. Vertex AI에서 세션 생성
            print(f"[SessionService] Creating Vertex AI session for user_id: {user_id}")
            vertex_session = await self.vertex_session_service.create_session(
                app_name=self.app_name,
                user_id=str(user_id)  # Vertex AI는 문자열 user_id 사용
            )

            print(f"[SessionService] ✅ Vertex AI session created:")
            print(f"    - vertex_session.id: {vertex_session.id}")
            print(f"    - app_name: {self.app_name}")
            print(f"    - user_id: {user_id}")

            # 2. DB에 메타데이터 저장
            session_entity = ChatSession.create(
                user_id=user_id,
                vertex_session_id=vertex_session.id,  # Vertex AI 세션 ID
                title=title
            )

            saved_session = self.repo.save(session_entity)

            print(f"[SessionService] Created session: {saved_session.sid}")
            print(f"    - DB session.id: {saved_session.id}")
            print(f"    - DB session.sid: {saved_session.sid}")
            print(f"    - vertex_session_id: {saved_session.vertex_session_id}")
            return saved_session

        except Exception as e:
            print(f"[SessionService] Failed to create session: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_session_sync(self, user_id: int, title: str = "새로운 대화") -> ChatSession:
        """
        동기 버전 - FastAPI에서 사용
        """
        return asyncio.run(self.create_session(user_id, title))
    
    def get_session_by_sid(self, sid: UUID) -> Optional[ChatSession]:
        """SID로 세션 조회 (DB에서만)"""
        return self.repo.find_by_sid(sid)
    
    def get_session_by_id(self, id: int) -> Optional[ChatSession]:
        """내부 ID로 세션 조회 (DB에서만)"""
        return self.repo.find_by_id(id)
    
    def list_user_sessions(self, user_id: int, include_inactive: bool = False) -> List[ChatSession]:
        """사용자의 세션 목록 조회 (DB에서만)"""
        if include_inactive:
            return self.repo.find_all_by_user(user_id)
        else:
            return self.repo.find_active_by_user(user_id)
    
    def deactivate_session(self, sid: UUID) -> bool:
        """세션 비활성화 (DB에서만, Vertex AI 세션은 유지)"""
        success = self.repo.update_active_status(sid, False)
        if success:
            print(f"[SessionService] Deactivated session: {sid}")
        return success
    
    def update_session_title(self, sid: UUID, new_title: str) -> bool:
        """세션 제목 업데이트 (DB에서만)"""
        return self.repo.update_title(sid, new_title)
    
    async def delete_vertex_session(self, user_id: int, session_id: str):
        """
        Vertex AI 세션 삭제

        Args:
            user_id: 사용자 ID
            session_id: Vertex AI 세션 ID
        """
        try:
            await self.vertex_session_service.delete_session(
                app_name=self.app_name,
                user_id=str(user_id),
                session_id=session_id
            )
            print(f"[SessionService] Deleted Vertex AI session: {session_id}")
        except Exception as e:
            print(f"[SessionService] Failed to delete Vertex AI session: {e}")

    async def get_vertex_session(self, user_id: int, session_id: str):
        """
        Vertex AI 세션 조회 (존재 여부 확인용)

        Args:
            user_id: 사용자 ID
            session_id: Vertex AI 세션 ID

        Returns:
            Session object if exists, None otherwise
        """
        try:
            session = await self.vertex_session_service.get_session(
                app_name=self.app_name,
                user_id=str(user_id),
                session_id=session_id
            )
            print(f"[SessionService] ✅ Vertex AI session found: {session_id}")
            return session
        except Exception as e:
            print(f"[SessionService] ❌ Vertex AI session not found or error: {e}")
            return None


# Dependency Injection을 위한 싱글톤 팩토리
_session_service_instance: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """
    SessionService 싱글톤 인스턴스 반환
    
    FastAPI Dependency로 사용됩니다.
    """
    global _session_service_instance
    
    if _session_service_instance is None:
        from supabase import create_client
        from urllib.parse import urlparse
        
        # DATABASE_URL에서 Supabase URL 추출
        # 형식: postgresql://postgres.{project_ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres
        db_url = config.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL is not configured")
        
        parsed = urlparse(db_url)
        username = parsed.username  # postgres.{project_ref}
        
        if username and '.' in username:
            project_ref = username.split('.', 1)[1]
            supabase_url = f"https://{project_ref}.supabase.co"
        else:
            raise ValueError("Invalid DATABASE_URL format: cannot extract project_ref")
        
        # API 키는 config에서 가져오기 (Cloud Run 환경 변수 또는 Secret Manager)
        supabase_key = config.SUPABASE_KEY
        if not supabase_key:
            raise ValueError("SUPABASE_KEY (DATABASE_KEY) is not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        session_repo = ChatSessionRepository(supabase)
        _session_service_instance = SessionService(session_repo)
    
    return _session_service_instance

