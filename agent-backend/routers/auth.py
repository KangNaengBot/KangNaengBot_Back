"""
Google OAuth 인증 라우터
"""

import uuid
import requests
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy import create_engine, text
from typing import Optional

import config
from utils.jwt import create_access_token, verify_token

router = APIRouter()

# Google OAuth 설정
GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Google OAuth 클라이언트 설정
CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [config.OAUTH_REDIRECT_URI],
    }
}


@router.get("/google/login")
async def google_login():
    """
    Google OAuth 로그인 URL로 리다이렉트
    """
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth credentials not configured")

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=GOOGLE_OAUTH_SCOPES,
        redirect_uri=config.OAUTH_REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None):
    """
    Google OAuth 콜백 처리

    1. Authorization code로 access token 교환
    2. Google userinfo에서 사용자 정보 조회
    3. DB에 사용자 upsert
    4. JWT 토큰 발급
    """
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth credentials not configured")

    try:
        # OAuth flow로 토큰 교환
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=GOOGLE_OAUTH_SCOPES,
            redirect_uri=config.OAUTH_REDIRECT_URI
        )
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Google userinfo API 호출
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        userinfo = userinfo_response.json()

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")

        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Invalid user info from Google")

        # DB에 사용자 upsert
        user_id = await upsert_user(google_id, email, name)

        # JWT 토큰 생성
        access_token = create_access_token(data={"user_id": str(user_id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user_id),
                "email": email,
                "name": name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.get("/me")
async def get_current_user(authorization: str = Header(...)):
    """
    현재 로그인된 사용자 정보 조회

    Authorization 헤더에서 Bearer 토큰을 추출하여 검증
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # DB에서 사용자 정보 조회
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def upsert_user(google_id: str, email: str, name: str) -> uuid.UUID:
    """
    사용자 정보를 DB에 upsert (없으면 생성, 있으면 업데이트)

    Returns:
        사용자 UUID
    """
    if not config.DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database not configured")

    engine = create_engine(config.DATABASE_URL)

    with engine.connect() as connection:
        # google_id로 기존 사용자 조회
        result = connection.execute(
            text("SELECT id FROM profiles WHERE google_id = :google_id"),
            {"google_id": google_id}
        )
        existing_user = result.fetchone()

        if existing_user:
            # 기존 사용자 - 이메일, 이름 업데이트
            connection.execute(
                text("""
                    UPDATE profiles
                    SET email = :email, name = :name
                    WHERE google_id = :google_id
                """),
                {"email": email, "name": name, "google_id": google_id}
            )
            connection.commit()
            return existing_user[0]
        else:
            # 신규 사용자 생성
            new_id = uuid.uuid4()
            connection.execute(
                text("""
                    INSERT INTO profiles (id, google_id, email, name, created_at)
                    VALUES (:id, :google_id, :email, :name, NOW())
                """),
                {"id": new_id, "google_id": google_id, "email": email, "name": name}
            )
            connection.commit()
            return new_id


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    UUID로 사용자 정보 조회
    """
    if not config.DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database not configured")

    engine = create_engine(config.DATABASE_URL)

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT id, google_id, email, name, student_id, college,
                       department, major, graduation_status, current_semester, created_at
                FROM profiles
                WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row[0]),
            "google_id": row[1],
            "email": row[2],
            "name": row[3],
            "student_id": row[4],
            "college": row[5],
            "department": row[6],
            "major": row[7],
            "graduation_status": row[8],
            "current_semester": row[9],
            "created_at": row[10].isoformat() if row[10] else None
        }
