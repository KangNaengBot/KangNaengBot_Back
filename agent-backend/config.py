"""
환경 변수 설정
"""

import os
from pathlib import Path
from dotenv import load_dotenv
try:
    from google_adk.config.secrets import get_secret
except ImportError:
    # 로컬 실행 시 경로 문제 해결을 위한 처리
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from google_adk.config.secrets import get_secret

# .env 파일 로드 (루트 디렉토리의 .env 파일 우선)
root_env = Path(__file__).parent.parent / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

# Agent Engine 설정
AGENT_RESOURCE_ID = os.getenv(
    "AGENT_RESOURCE_ID",
    "projects/88199591627/locations/us-east4/reasoningEngines/4725225987158048768"
)

# Google Cloud 설정 (하드코딩)
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-east4")

# Database 설정 (Secret Manager -> 환경 변수 fallback)
DATABASE_URL = get_secret("DATABASE_URL", default=os.getenv("DATABASE_URL"))

# OAuth 설정
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "88199591627-a603fsufai3053h47i66hogsbs5gb6pn.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET", default=os.getenv("GOOGLE_CLIENT_SECRET"))
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/google/callback")

# Supabase 설정 (사용하지 않으면 None)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# JWT 설정
JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY", default=os.getenv("JWT_SECRET_KEY"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# 환경 확인
def check_config():
    """환경 변수 확인"""
    required_vars = {
        "AGENT_RESOURCE_ID": AGENT_RESOURCE_ID,
        "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
        "VERTEX_AI_LOCATION": VERTEX_AI_LOCATION,
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return required_vars

