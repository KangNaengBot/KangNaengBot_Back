# Agent Backend API

강남대학교 Multi-Agent 챗봇 백엔드 API

## 🚀 빠른 시작

### 로컬 개발

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 수정 (AGENT_RESOURCE_ID 등)

# 3. 서버 실행
uvicorn main:app --reload --port 8080
```

서버 실행 후: http://localhost:8080

### API 문서

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 📋 API 엔드포인트

### 1. 새 채팅 시작

```bash
POST /chat/new
```

**응답:**
```json
{
  "user_id": "anon_a1b2c3d4",
  "session_id": "1234567890",
  "message": "새 채팅이 시작되었습니다."
}
```

### 2. 메시지 전송 (스트리밍)

```bash
POST /chat/message
Content-Type: application/json

{
  "user_id": "anon_a1b2c3d4",
  "session_id": "1234567890",
  "message": "2024년 공과대학 졸업 요건 알려줘"
}
```

**응답:** SSE (Server-Sent Events) 스트리밍

```
data: {"text": "2024년 공과대학 졸업요건은...", "done": false}
data: {"text": "기초교양 17학점...", "done": false}
data: {"text": "", "done": true}
```

### 3. 헬스체크

```bash
GET /health
```

## 🌐 Cloud Run 배포

### 소스 기반 배포 (도커 없이)

```bash
# 프로젝트 루트에서 실행
gcloud run deploy agent-backend-api \
  --source=./agent-backend \
  --region=us-east4 \
  --allow-unauthenticated \
  --set-env-vars="AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664,GOOGLE_CLOUD_PROJECT=kangnam-backend,VERTEX_AI_LOCATION=us-east4" \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --memory=512Mi
```

### 배포 후 테스트

```bash
# 배포된 URL 확인
gcloud run services describe agent-backend-api --region=us-east4 --format="value(status.url)"

# 새 채팅 시작
curl -X POST https://agent-backend-api-xxx.run.app/chat/new

# 메시지 전송
curl -X POST https://agent-backend-api-xxx.run.app/chat/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"anon_xxx","session_id":"yyy","message":"안녕"}'
```

## 🔧 로컬 테스트

### curl로 테스트

```bash
# 새 채팅
curl -X POST http://localhost:8080/chat/new

# 메시지 전송 (스트리밍 확인)
curl -X POST http://localhost:8080/chat/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"anon_test","session_id":"123","message":"안녕"}' \
  -N  # 버퍼링 비활성화
```

### Python으로 테스트

```python
import requests
import json

# 새 채팅
response = requests.post("http://localhost:8080/chat/new")
data = response.json()
print(f"User ID: {data['user_id']}")
print(f"Session ID: {data['session_id']}")

# 메시지 전송 (스트리밍)
response = requests.post(
    "http://localhost:8080/chat/message",
    json={
        "user_id": data['user_id'],
        "session_id": data['session_id'],
        "message": "2024년 졸업 요건"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        text = line.decode('utf-8')
        if text.startswith('data: '):
            event = json.loads(text[6:])
            print(event['text'], end='', flush=True)
```

## 📦 프로젝트 구조

```
agent-backend/
├── main.py                 # FastAPI 앱
├── config.py               # 환경 변수
├── routers/
│   ├── __init__.py
│   └── chat.py            # 채팅 API
├── services/
│   ├── __init__.py
│   └── chat_service.py    # Agent Engine 통신
├── requirements.txt        # 의존성
├── .env.example           # 환경 변수 예시
└── README.md
```

## 🔑 환경 변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `AGENT_RESOURCE_ID` | Agent Engine 리소스 ID | `projects/.../reasoningEngines/...` |
| `GOOGLE_CLOUD_PROJECT` | GCP 프로젝트 ID | `kangnam-backend` |
| `VERTEX_AI_LOCATION` | Vertex AI 리전 | `us-east4` |

## 📦 Requirements 관리

### 왜 두 개의 requirements.txt가 있나요?

프로젝트에는 **2개의 독립적인 배포 대상**이 있습니다:

1. **프로젝트 루트** (`../requirements.txt`)
   - **용도**: Agent Engine 배포 (Vertex AI)
   - **포함**: 전체 애플리케이션 패키지 (supabase, beautifulsoup4, google-genai 등)

2. **agent-backend** (`./requirements.txt`)
   - **용도**: FastAPI 백엔드 API (Cloud Run)
   - **포함**: 백엔드 API에 필요한 패키지만
   - **이유**: Cloud Run Buildpack이 이 디렉토리만 보고 빌드

### 패키지 추가 방법

1. **루트 requirements.txt 수정**
   ```bash
   cd ..  # 프로젝트 루트로 이동
   nano requirements.txt  # 패키지 추가
   ```

2. **백엔드 requirements 동기화** (필요시)
   ```bash
   cd agent-backend
   ./sync_requirements.sh  # 백엔드용으로 동기화
   ```

3. **설치**
   ```bash
   source ../.venv/bin/activate
   uv pip install -r requirements.txt
   ```

### ⚠️ 중요: psycopg 사용

이 백엔드는 PostgreSQL 비동기 연결을 위해 **psycopg3**를 사용합니다:
- ✅ 사용: `psycopg[binary,pool]==3.2.1`
- ❌ 사용 안 함: `psycopg2-binary`

## 🐛 트러블슈팅

### "Missing required environment variables"

→ `.env` 파일을 `.env.example`에서 복사하고 값 설정

### "Permission denied"

→ `gcloud auth application-default login` 실행

### 스트리밍이 안 됨

→ Cloud Run 배포 시 `--timeout=300` 설정 확인

## 📚 관련 문서

- Agent Engine 배포: `../DEPLOYMENT.md`
- 프론트엔드 연동: (추후 작성)

