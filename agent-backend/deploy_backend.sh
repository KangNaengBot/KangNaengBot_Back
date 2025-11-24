#!/bin/bash

# Agent Backend API를 Cloud Run에 배포하는 스크립트
# 프로젝트 루트에서 전체 컨텍스트를 포함하여 배포합니다.

set -e  # 에러 발생 시 중단

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Agent Backend API - Cloud Run 배포  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. 프로젝트 루트로 이동 (스크립트 위치 기준 상위 디렉토리)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}[1/5]${NC} 프로젝트 루트로 이동: $(pwd)"

# 2. 환경 변수 로드
if [ -f .env ]; then
    echo -e "${YELLOW}[2/5]${NC} .env 파일에서 환경 변수 로드 중..."
    set -a
    source .env
    set +a
    echo "  ✓ .env 파일 로드 완료"
else
    echo -e "${RED}에러: .env 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

# 3. 필수 환경 변수 확인
echo -e "${YELLOW}[3/5]${NC} 환경 변수 확인 중..."
if [ -z "$AGENT_RESOURCE_ID" ]; then
    echo -e "${RED}에러: AGENT_RESOURCE_ID가 설정되지 않았습니다.${NC}"
    exit 1
fi

echo "  ✓ AGENT_RESOURCE_ID: $AGENT_RESOURCE_ID"
echo "  ✓ GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-kangnam-backend}"
echo "  ✓ VERTEX_AI_LOCATION: ${VERTEX_AI_LOCATION:-us-east4}"

# 4. 배포 설정
SERVICE_NAME="agent-backend-api"
REGION="${VERTEX_AI_LOCATION:-us-east4}"
PROJECT="${GOOGLE_CLOUD_PROJECT:-kangnam-backend}"

echo -e "${YELLOW}[4/5]${NC} 배포 설정:"
echo "  • 서비스 이름: $SERVICE_NAME"
echo "  • 리전: $REGION"
echo "  • 프로젝트: $PROJECT"
echo "  • 소스 위치: $(pwd) (프로젝트 루트)"
echo ""

# 5. Cloud Run 배포 (소스 기반, 루트 컨텍스트)
echo -e "${YELLOW}[5/5]${NC} Cloud Run에 배포 중..."
echo "  (Buildpack이 pyproject.toml을 감지하여 빌드합니다)"
echo ""

gcloud run deploy "$SERVICE_NAME" \
  --source=. \
  --region="$REGION" \
  --project="$PROJECT" \
  --allow-unauthenticated \
  --set-env-vars="AGENT_RESOURCE_ID=$AGENT_RESOURCE_ID,GOOGLE_CLOUD_PROJECT=$PROJECT,VERTEX_AI_LOCATION=$REGION,DATABASE_URL=$DATABASE_URL,JWT_SECRET_KEY=$JWT_SECRET_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_KEY=$SUPABASE_KEY,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET" \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --memory=1Gi \
  --cpu=1 \
  --platform=managed

# 배포 완료
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  배포 완료! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT" \
  --format="value(status.url)")

echo -e "${GREEN}서비스 URL:${NC} $SERVICE_URL"
echo ""
echo -e "${YELLOW}테스트 명령어:${NC}"
echo "curl -X POST $SERVICE_URL/chat/new"
