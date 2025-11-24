"""
세션 관리 서비스
"""
import uuid
from typing import Dict, List, Optional
import vertexai
from vertexai import agent_engines
import config
from supabase import create_client, Client

class SessionManager:
    """
    Vertex AI Agent Engine 세션 관리자
    
    - 세션 생성 (Create): Vertex AI + Supabase DB
    - 세션 조회 (Get): 로컬 캐시 -> DB
    - 세션 목록 조회 (List): Supabase DB
    """
    
    def __init__(self):
        """Agent Engine 및 Supabase 초기화"""
        from urllib.parse import urlparse
        
        self.engine = agent_engines.get(config.AGENT_RESOURCE_ID)
        # 로컬 세션 캐시 (sid -> {id, vertex_session_id})
        self._local_session_map: Dict[str, Dict[str, Any]] = {}
        
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
        
        # Supabase 클라이언트 초기화
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def create_session(self, user_id: int) -> str:
        """
        새 세션 생성
        
        Args:
            user_id: 사용자 ID (DB PK, int)
            
        Returns:
            sid: 세션 식별자 (UUID, str) - 프론트엔드 제공용
        """
        try:
            # 1. Vertex AI에서 세션 생성
            # Vertex AI는 user_id(str)를 요구하므로 int -> str 변환
            vertex_session = self.engine.create_session(user_id=str(user_id))
            vertex_session_id = vertex_session.name.split('/')[-1]
            
            # 2. Supabase DB에 세션 저장
            session_data = {
                "user_id": user_id,
                "vertex_session_id": vertex_session_id,
                "title": "새로운 대화",
                "is_active": True
            }
            
            # insert 후 id(BIGINT)와 sid(UUID) 반환
            response = self.supabase.table("chat_sessions") \
                .insert(session_data) \
                .select("id, sid") \
                .execute()
            
            if response.data:
                db_id = response.data[0]['id'] # BIGINT
                sid = response.data[0]['sid']  # UUID
                
                # 로컬 맵 업데이트 (sid -> {id, vertex_session_id})
                self._local_session_map[sid] = {
                    "id": db_id,
                    "vertex_session_id": vertex_session_id
                }
                
                print(f"[SessionManager] New session created: {sid} (DB ID: {db_id})")
                return sid
            else:
                raise Exception("Failed to insert session into DB")
            
        except Exception as e:
            print(f"[SessionManager] Failed to create session: {e}")
            # 실패 시 임시 UUID 반환 (서비스 중단 방지)
            return str(uuid.uuid4())

    def get_session_info(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        SID로 세션 정보 조회
        
        Args:
            sid: 세션 UUID
            
        Returns:
            {"id": int, "vertex_session_id": str} 또는 None
        """
        # 1. 로컬 캐시 확인
        if sid in self._local_session_map:
            return self._local_session_map[sid]
            
        # 2. DB 조회
        try:
            response = self.supabase.table("chat_sessions") \
                .select("id, vertex_session_id") \
                .eq("sid", sid) \
                .single() \
                .execute()
                
            if response.data:
                session_info = {
                    "id": response.data['id'],
                    "vertex_session_id": response.data['vertex_session_id']
                }
                self._local_session_map[sid] = session_info
                return session_info
                
        except Exception as e:
            print(f"[SessionManager] Failed to get session info: {e}")
            
        return None

    def list_sessions(self, user_id: int) -> List[Dict]:
        """
        사용자의 과거 세션 목록 조회
        """
        try:
            response = self.supabase.table("chat_sessions") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .execute()
            return response.data
        except Exception as e:
            print(f"[SessionManager] Failed to list sessions: {e}")
            return []

# 싱글톤 인스턴스
_session_manager_instance = None

def get_session_manager() -> SessionManager:
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance
