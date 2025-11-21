"""
GET /sessions - 세션 목록 조회
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime

from services.session_service import SessionService, get_session_service
from utils.dependencies import get_current_user

router = APIRouter()


class SessionItem(BaseModel):
    """세션 목록 항목"""
    sid: str
    title: str
    is_active: bool
    created_at: datetime


class ListSessionsResponse(BaseModel):
    """세션 목록 응답"""
    sessions: List[SessionItem]


@router.get("/", response_model=ListSessionsResponse)
async def list_sessions(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    세션 목록 조회
    
    현재 로그인된 유저의 세션 목록을 반환합니다.
    
    Headers:
        Authorization: Bearer {access_token}
    
    Query Parameters:
        include_inactive: 비활성 세션 포함 여부 (기본값: False)
    
    Returns:
        sessions: 세션 목록 (최신순)
    """
    user_id = current_user["id"]
    
    sessions = session_service.list_user_sessions(
        user_id=user_id,
        include_inactive=include_inactive
    )
    
    return ListSessionsResponse(
        sessions=[
            SessionItem(
                sid=str(s.sid),
                title=s.title,
                is_active=s.is_active,
                created_at=s.created_at
            )
            for s in sessions
        ]
    )
