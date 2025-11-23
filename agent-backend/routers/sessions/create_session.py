"""
POST /sessions - 새 세션 생성
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from utils.dependencies import get_current_user
from services.session_service import SessionService, get_session_service

router = APIRouter()


class CreateSessionResponse(BaseModel):
    """세션 생성 응답"""
    session_id: str
    user_id: int
    title: str
    created_at: Optional[str] = None


@router.post("/", response_model=CreateSessionResponse)
async def create_session(
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    새로운 채팅 세션 생성
    
    Headers:
        Authorization: Bearer {access_token}
    
    Returns:
        session_id: 세션 UUID
        user_id: 사용자 ID
        title: "새로운 대화" (첫 메시지 전송 시 자동 업데이트)
        created_at: 생성 시각
        message: 성공 메시지
        
    Note:
        세션 생성 직후 첫 메시지를 보내면, 해당 메시지가 title로 설정됩니다.
    """
    user_id = int(current_user["id"])
    
    try:
        # Vertex AI Session Service를 통해 세션 생성 (title은 기본값)
        session = await session_service.create_session(user_id=user_id)
        
        return CreateSessionResponse(
            session_id=str(session.sid),
            user_id=user_id,
            title=session.title,  # "새로운 대화"
            created_at=session.created_at.isoformat() if session.created_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )
