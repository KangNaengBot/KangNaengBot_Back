#!/bin/bash
# test_rag Agent 업데이트 스크립트 (Blue-Green 배포)

set -e          # 에러 발생 시 중단
set -o pipefail # 파이프라인에서도 에러 감지

echo "🔄 Agent 업데이트 시작..."
echo ""

# Google Cloud 설정
PROJECT_ID="kangnam-backend"

# 현재 배포된 Resource ID 읽기 (Secret Manager에서)
CURRENT_ID=$(gcloud secrets versions access latest --secret=AGENT_RESOURCE_ID --project=$PROJECT_ID 2>/dev/null || echo "")

# 파이썬 명령어 설정 (가상환경 우선)
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python"
fi

if [ -z "$CURRENT_ID" ]; then
    echo "⚠️  Secret Manager에 AGENT_RESOURCE_ID가 없습니다."
    echo "   초기 배포를 실행합니다..."
    echo ""
    
    # 가상환경 활성화
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # 초기 배포 (실시간 로그 표시)
    INITIAL_OUTPUT=$(mktemp)
    $PYTHON_CMD deploy.py --create 2>&1 | tee "$INITIAL_OUTPUT"
    
    # Resource ID 추출 (이모지 때문에 4번째 필드)
    INITIAL_RESOURCE_ID=$(grep "Resource ID:" "$INITIAL_OUTPUT" | awk '{print $4}')
    rm -f "$INITIAL_OUTPUT"
    
    if [ -z "$INITIAL_RESOURCE_ID" ]; then
        echo ""
        echo "❌ 배포 실패!"
        exit 1
    fi
    
    echo ""
    echo "✅ 배포 완료: $INITIAL_RESOURCE_ID"
    echo ""
    echo "📝 Secret Manager에 자동 등록 중..."
    
    # Secret Manager에 저장 (없으면 생성, 있으면 새 버전 추가)
    if gcloud secrets describe AGENT_RESOURCE_ID --project=$PROJECT_ID &>/dev/null; then
        echo "$INITIAL_RESOURCE_ID" | gcloud secrets versions add AGENT_RESOURCE_ID --data-file=- --project=$PROJECT_ID
    else
        echo "$INITIAL_RESOURCE_ID" | gcloud secrets create AGENT_RESOURCE_ID --data-file=- --project=$PROJECT_ID
    fi
    
    echo "✅ Secret Manager 업데이트 완료!"
    echo ""
    echo "=" | tr '=' '=' | head -c 70
    echo ""
    echo "🎉 초기 배포 완료!"
    echo "=" | tr '=' '=' | head -c 70
    echo ""
    echo "📌 Resource ID: $INITIAL_RESOURCE_ID"
    echo ""
    echo "🔑 다음 단계:"
    echo "   1. 세션 생성:"
    echo "      $PYTHON_CMD deploy.py --create_session --resource_id=\"$INITIAL_RESOURCE_ID\""
    echo ""
    echo "   2. 메시지 전송:"
    echo "      $PYTHON_CMD deploy.py --send --resource_id=\"$INITIAL_RESOURCE_ID\" --session_id=\"세션ID\" --message=\"테스트\""
    echo ""
    exit 0
fi

echo "📌 현재 배포: $CURRENT_ID"
echo ""

# 새 버전 배포
echo "🚀 새 버전 배포 중..."
echo ""

# 가상환경 활성화
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 배포 출력을 파일에 저장하면서 실시간으로 표시
DEPLOY_OUTPUT=$(mktemp)
$PYTHON_CMD deploy.py --create 2>&1 | tee "$DEPLOY_OUTPUT"

# Resource ID 추출 (이모지 때문에 4번째 필드)
NEW_RESOURCE_ID=$(grep "Resource ID:" "$DEPLOY_OUTPUT" | awk '{print $4}')
rm -f "$DEPLOY_OUTPUT"

if [ -z "$NEW_RESOURCE_ID" ]; then
    echo ""
    echo "❌ 배포 실패!"
    exit 1
fi

echo ""
echo "✅ 새 버전 배포 완료: $NEW_RESOURCE_ID"
echo ""

# 테스트 세션 생성
echo "🧪 새 버전 테스트 중..."

# 세션 생성 시도 (에러 로그 저장)
SESSION_OUTPUT=$($PYTHON_CMD deploy.py --create_session --resource_id="$NEW_RESOURCE_ID" 2>&1)
TEST_SESSION=$(echo "$SESSION_OUTPUT" | grep "Session ID:" | awk '{print $3}')

if [ -z "$TEST_SESSION" ]; then
    echo "❌ 세션 생성 실패!"
    echo ""
    echo "📋 에러 로그:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$SESSION_OUTPUT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   새 배포를 삭제합니다..."
    $PYTHON_CMD deploy.py --delete --resource_id="$NEW_RESOURCE_ID"
    exit 1
fi

echo "✅ 테스트 세션 생성: $TEST_SESSION"
echo ""

# 간단한 테스트 메시지
echo "📨 테스트 메시지 전송 중..."

# 테스트 메시지 전송 (에러 로그 저장)
MESSAGE_OUTPUT=$($PYTHON_CMD deploy.py --send \
    --resource_id="$NEW_RESOURCE_ID" \
    --session_id="$TEST_SESSION" \
    --message="안녕" 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ 테스트 통과!"
else
    echo "❌ 테스트 실패!"
    echo ""
    echo "📋 에러 로그:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$MESSAGE_OUTPUT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   새 배포를 삭제합니다..."
    $PYTHON_CMD deploy.py --delete --resource_id="$NEW_RESOURCE_ID"
    exit 1
fi

echo ""
echo "🔄 Secret Manager 업데이트 중..."

# 이전 버전을 백업 시크릿에 저장
echo "$CURRENT_ID" | gcloud secrets versions add AGENT_RESOURCE_ID_BACKUP --data-file=- --project=$PROJECT_ID 2>/dev/null || \
    echo "$CURRENT_ID" | gcloud secrets create AGENT_RESOURCE_ID_BACKUP --data-file=- --project=$PROJECT_ID

# 새 버전을 메인 시크릿에 저장
echo "$NEW_RESOURCE_ID" | gcloud secrets versions add AGENT_RESOURCE_ID --data-file=- --project=$PROJECT_ID

echo ""
echo "=" | tr '=' '=' | head -c 70
echo ""
echo "✅ 업데이트 완료!"
echo "=" | tr '=' '=' | head -c 70
echo ""
echo "📌 새 버전: $NEW_RESOURCE_ID"
echo "💾 이전 버전 (롤백용): $CURRENT_ID"
echo ""
echo "⚠️  프로덕션 환경에 적용하기 전에 충분히 테스트하세요!"
echo ""
echo "🔙 롤백이 필요하면:"
echo "   1. 새 버전 삭제:"
echo "      $PYTHON_CMD deploy.py --delete --resource_id=\"$NEW_RESOURCE_ID\""
echo ""
echo "   2. 이전 버전으로 복구:"
echo "      echo '$CURRENT_ID' | gcloud secrets versions add AGENT_RESOURCE_ID --data-file=- --project=$PROJECT_ID"
echo ""
echo "✅ 문제없으면 이전 버전 삭제:"
echo "   $PYTHON_CMD deploy.py --delete --resource_id=\"$CURRENT_ID\""
echo ""

