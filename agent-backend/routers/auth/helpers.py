"""
Auth 헬퍼 함수들
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional


async def upsert_user(db: AsyncSession, google_id: str, email: str, name: str) -> str:
    """
    사용자 정보를 DB에 upsert (비동기)
    
    Returns:
        user_id: BIGINT (자동 증가 ID의 문자열 표현)
    """
    # google_id로 기존 사용자 조회 (users 테이블)
    result = await db.execute(
        text("SELECT id FROM users WHERE google_id = :google_id"),
        {"google_id": google_id}
    )
    existing_user = result.fetchone()

    if existing_user:
        # 기존 사용자 - 이메일, 이름 업데이트
        await db.execute(
            text("""
                UPDATE users
                SET email = :email, name = :name, updated_at = NOW()
                WHERE google_id = :google_id
            """),
            {"email": email, "name": name, "google_id": google_id}
        )
        await db.commit()
        return str(existing_user[0])  # BIGINT를 문자열로 변환
    else:
        # 신규 사용자 생성 (id와 sid는 DB에서 자동 생성)
        result = await db.execute(
            text("""
                INSERT INTO users (google_id, email, name, created_at, updated_at)
                VALUES (:google_id, :email, :name, NOW(), NOW())
                RETURNING id
            """),
            {"google_id": google_id, "email": email, "name": name}
        )
        new_user = result.fetchone()
        await db.commit()
        return str(new_user[0])  # BIGINT를 문자열로 변환


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[dict]:
    """
    ID로 사용자 정보 조회 (비동기)
    
    users 테이블에서 기본 정보를 조회합니다.
    """
    result = await db.execute(
        text("""
            SELECT id, sid, google_id, email, name, created_at, updated_at
            FROM users
            WHERE id = :user_id
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()

    if not row:
        return None

    return {
        "id": str(row[0]),  # BIGINT
        "sid": str(row[1]) if row[1] else None,  # UUID
        "google_id": row[2],
        "email": row[3],
        "name": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
        "updated_at": row[6].isoformat() if row[6] else None
    }


async def check_user_exists_by_email(db: AsyncSession, email: str) -> bool:
    """
    이메일로 사용자 존재 여부 확인 (비동기)
    
    Args:
        db: 데이터베이스 세션
        email: 확인할 이메일 주소
    
    Returns:
        사용자가 존재하면 True, 없으면 False
    """
    result = await db.execute(
        text("SELECT COUNT(*) FROM users WHERE email = :email"),
        {"email": email}
    )
    count = result.scalar()
    return count > 0 if count is not None else False


async def check_user_exists_by_google_id(db: AsyncSession, google_id: str) -> bool:
    """
    Google ID로 사용자 존재 여부 확인 (비동기)
    
    Args:
        db: 데이터베이스 세션
        google_id: 확인할 Google ID
    
    Returns:
        사용자가 존재하면 True, 없으면 False
    """
    result = await db.execute(
        text("SELECT COUNT(*) FROM users WHERE google_id = :google_id"),
        {"google_id": google_id}
    )
    count = result.scalar()
    return count > 0 if count is not None else False