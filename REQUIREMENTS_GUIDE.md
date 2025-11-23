# Requirements.txt 관리 가이드

## 📂 프로젝트 구조

```
GangNangBot/
├── requirements.txt               # ← Agent Engine 배포용 (Vertex AI)
├── goole_adk/                     # Multi-Agent 시스템
├── deploy.py                      # Agent Engine 배포 스크립트
├── update_deployment.sh           # Agent 업데이트 스크립트
│
└── agent-backend/
    ├── requirements.txt           # ← FastAPI 백엔드 배포용 (Cloud Run)
    ├── deploy_backend.sh          # 백엔드 배포 스크립트
    ├── main.py                    # FastAPI 앱
    └── sync_requirements.sh       # 🆕 Requirements 동기화 스크립트
```

## 🎯 왜 두 개가 필요한가요?

### 배포 방식의 차이

| 특징 | 프로젝트 루트 | agent-backend |
|------|------------|--------------|
| **배포 대상** | Vertex AI Agent Engine | Cloud Run (FastAPI API) |
| **배포 스크립트** | `deploy.py` | `deploy_backend.sh` |
| **배포 명령어** | `python deploy.py --create` | `gcloud run deploy --source=.` |
| **패키징 범위** | 전체 프로젝트 + `goole_adk/` | `agent-backend/` 디렉토리만 |
| **필요 패키지** | Agent + 데이터 크롤링 + 인증 | FastAPI + 데이터베이스 + 인증 |

### 핵심 이유

`deploy_backend.sh`에서 **Cloud Run Buildpack**을 사용할 때:
```bash
gcloud run deploy agent-backend-api \
  --source=.  # ← 현재 디렉토리(agent-backend/)만 업로드!
```

- Buildpack은 `agent-backend/` 디렉토리**만** 접근 가능
- 상위 디렉토리의 `../requirements.txt`는 접근 불가
- 따라서 `agent-backend/requirements.txt`가 **반드시 필요**

## 📋 패키지 비교

### 루트 requirements.txt (전체)
```txt
# FastAPI 및 서버
fastapi==0.119.1
uvicorn[standard]==0.38.0
pydantic==2.12.3

# Google Cloud & Vertex AI
google-cloud-aiplatform==1.122.0
vertexai==1.43.0
google-adk==1.16.0
google-genai==1.46.0          # ← Agent Engine용

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

# 기타
supabase==2.24.0              # ← Agent Engine용
beautifulsoup4==4.12.3        # ← 데이터 크롤링용
```

### agent-backend/requirements.txt (백엔드만)
```txt
# FastAPI 및 서버
fastapi==0.119.1
uvicorn[standard]==0.38.0
pydantic==2.12.3

# Google Cloud & Vertex AI (프로젝트 루트와 동일 버전)
google-cloud-aiplatform==1.122.0
vertexai==1.43.0
google-adk==1.16.0
# ❌ google-genai 제외 (불필요)

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
# ❌ supabase, beautifulsoup4 제외 (불필요)
```

## 🔄 동기화 방법

### 자동 동기화 (권장)

```bash
cd agent-backend
./sync_requirements.sh
```

이 스크립트는:
1. ✅ 백엔드에 필요한 패키지만 포함
2. ✅ 버전을 루트와 동일하게 유지
3. ✅ 불필요한 패키지(`google-genai`, `supabase`, `beautifulsoup4`) 제외

### 수동 동기화

1. **루트 requirements.txt 수정**
   ```bash
   cd GangNangBot
   nano requirements.txt  # 패키지 추가/수정
   ```

2. **agent-backend requirements.txt 수정**
   ```bash
   cd agent-backend
   nano requirements.txt  # 동일한 버전으로 업데이트
   ```

3. **설치 및 테스트**
   ```bash
   source ../.venv/bin/activate
   uv pip install -r requirements.txt
   ```

## ⚠️ 주의사항

### 1. psycopg 버전
- ✅ **사용**: `psycopg[binary,pool]==3.2.1` (비동기 지원)
- ❌ **사용 금지**: `psycopg2-binary` (구버전, 동기 전용)

**이유**: `routers/database.py`에서 `postgresql+psycopg://` (psycopg3) 사용

### 2. PyJWT 버전
- ✅ **사용**: `PyJWT==2.10.1`
- ❌ **사용 금지**: `PyJWT==2.9.0`

**이유**: `supabase==2.24.0`이 `PyJWT>=2.10.1` 요구

### 3. 버전 일관성
- 반드시 루트와 agent-backend의 **공통 패키지 버전을 일치**시킬 것
- 특히 다음 패키지들:
  - `fastapi`
  - `pydantic`
  - `google-cloud-aiplatform`
  - `vertexai`
  - `sqlalchemy`

## 🚀 배포 워크플로우

### Agent Engine 업데이트
```bash
cd GangNangBot
./update_deployment.sh
```
- 사용: **루트** `requirements.txt`
- 영향: Agent Engine만

### 백엔드 API 업데이트
```bash
cd agent-backend
./deploy_backend.sh
```
- 사용: **agent-backend** `requirements.txt`
- 영향: Cloud Run 백엔드 API만

## ✅ 결론

**두 개의 requirements.txt 모두 필요합니다!**

- **삭제 불가**: Cloud Run Buildpack이 agent-backend 디렉토리만 접근
- **해결책**: 동기화 스크립트(`sync_requirements.sh`)로 일관성 유지
- **장점**: 각 배포 환경에 최적화된 패키지만 설치 → 빌드 속도 향상

---

**마지막 업데이트**: 2025-11-23
