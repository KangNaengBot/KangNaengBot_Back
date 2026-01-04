"""
환경 변수 설정

Cloud Run 환경에서는 Secret Manager가 환경 변수로 자동 주입됩니다.
로컬 환경에서는 Secret Manager에서 직접 읽습니다.
"""

import os
from pathlib import Path

# Secret Manager 헬퍼 함수
try:
    from google_adk.config.secrets import get_secret
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from google_adk.config.secrets import get_secret

# Agent Engine 설정 (Secret Manager -> 환경 변수)
AGENT_RESOURCE_ID = get_secret("AGENT_RESOURCE_ID", default=os.getenv("AGENT_RESOURCE_ID"))

# Google Cloud 설정
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-east4")

# Database 설정 (Secret Manager -> 환경 변수)
DATABASE_URL = get_secret("DATABASE_URL", default=os.getenv("DATABASE_URL"))

# OAuth 설정
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "88199591627-a603fsufai3053h47i66hogsbs5gb6pn.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET", default=os.getenv("GOOGLE_CLIENT_SECRET"))

# Frontend URL (백엔드가 인증 후 프론트엔드로 리다이렉트할 때 사용)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kang-naeng-bot-fe.vercel.app")

# OAuth Redirect URI (Google이 백엔드로 콜백할 때 사용)
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", 
    "https://agent-backend-api-stcla4qgrq-uk.a.run.app/auth/google/callback"
)

# Supabase 설정 (Secret Manager -> 환경 변수)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = get_secret("DATABASE_KEY", default=os.getenv("DATABASE_KEY", os.getenv("SUPABASE_KEY")))

# JWT 설정 (Secret Manager -> 환경 변수)
JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY", default=os.getenv("JWT_SECRET_KEY"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Brevo 이메일 설정 (Secret Manager -> 환경 변수)
BREVO_API_KEY = get_secret("BREVO_API_KEY", default=os.getenv("BREVO_API_KEY"))
SENDER_NAME = os.getenv("SENDER_NAME", "강냉봇")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "kpj45123@gmail.com")
# Brevo 리스트 ID (캠페인 전송용)
BREVO_LIST_IDS = [int(x.strip()) for x in os.getenv("BREVO_LIST_IDS", "2").split(",") if x.strip()]

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

