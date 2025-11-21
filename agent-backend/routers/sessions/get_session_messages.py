"""
GET /sessions/{session_id}/messages - 세션 메시지 조회
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from services.chat_service import ChatService, get_chat_service
from services.session_service import SessionService, get_session_service
from utils.dependencies import get_current_user

router = APIRouter()


class MessageItem(BaseModel):
    """메시지 항목"""
    role: str
    content: str
    created_at: datetime


class GetMessagesResponse(BaseModel):
    """메시지 목록 응답"""
    session_id: str
    messages: List[MessageItem]


@router.get("/{session_id}/messages", response_model=GetMessagesResponse)
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    특정 세션의 메시지 내역 조회
    
    Headers:
        Authorization: Bearer {access_token}
    
    Path Parameters:
        session_id: 세션 UUID
    
    Query Parameters:
        limit: 조회할 메시지 수 제한 (선택)
    
    Returns:
        session_id: 세션 UUID
        messages: 메시지 목록 (시간순)
    """
    user_id = current_user["id"]
    
    # 세션 권한 확인
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    session = session_service.get_session_by_sid(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # 메시지 조회
    messages = chat_service.get_session_messages(session_uuid, limit=limit)
    
    return GetMessagesResponse(
        session_id=session_id,
        messages=[
            MessageItem(
                role=m.role,
                content=m.content,
                created_at=m.created_at
            )
            for m in messages
        ]
    )
