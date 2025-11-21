"""
Agent Backend API

FastAPI 백엔드 - Agent Engine과 연동
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware

# 새로운 라우터 구조
from routers.sessions import router as sessions_router
from routers.chat import router as chat_router
from routers.auth import router as auth_router
from routers import database

import config

# HTTPBearer security scheme (Swagger UI용)
security = HTTPBearer()

# FastAPI 앱 생성
app = FastAPI(
    title="Kangnam Agent API",
    description="강남대학교 Multi-Agent 챗봇 API",
    version="2.0.0",
    # Swagger UI에 Bearer 인증 추가
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 미들웨어 (OAuth State 관리용)
app.add_middleware(SessionMiddleware, secret_key=config.JWT_SECRET_KEY or "secret-key")

# 라우터 등록 (새로운 구조)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(database.router, prefix="/db", tags=["database"])

# 헬스체크 (Cloud Run 필수)
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "ok", "service": "agent-backend-api"}

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 정보"""
    return {
        "service": "Kangnam Agent API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "create_session": "POST /sessions",
            "list_sessions": "GET /sessions",
            "send_message": "POST /chat/message",
            "get_messages": "GET /sessions/{session_id}/messages",
            "delete_session": "DELETE /sessions/{session_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

