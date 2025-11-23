#!/bin/bash
# agent-backend/requirements.txt를 프로젝트 루트 requirements.txt와 동기화

set -e

echo "🔄 Syncing requirements.txt files..."

# 프로젝트 루트
ROOT_REQ="../requirements.txt"
BACKEND_REQ="./requirements.txt"

if [ ! -f "$ROOT_REQ" ]; then
    echo "❌ Root requirements.txt not found"
    exit 1
fi

# 백엔드 requirements를 루트로부터 생성
echo "📝 Updating agent-backend/requirements.txt from root..."

cat > "$BACKEND_REQ" << 'EOF'
# FastAPI 및 서버
fastapi==0.119.1
uvicorn[standard]==0.38.0
pydantic==2.12.3

# Google Cloud & Vertex AI (프로젝트 루트와 동일 버전)
google-cloud-aiplatform==1.122.0
vertexai==1.43.0
google-adk==1.16.0

# 환경 변수
python-dotenv==1.1.1

# OAuth & JWT
Authlib>=1.5.1
httpx>=0.28.1
PyJWT==2.10.1
itsdangerous==2.1.2

# Database
sqlalchemy==2.0.28
psycopg[binary,pool]==3.2.1
EOF

echo "✅ agent-backend/requirements.txt updated!"
echo ""
echo "💡 Note: agent-backend requirements is a subset of root requirements"
echo "        (excludes supabase, beautifulsoup4, google-genai)"
