"""
POST /chat/message - 메시지 전송 및 스트리밍 응답
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
import json

from slowapi import Limiter
from slowapi.util import get_remote_address

from services.chat_service import ChatService, get_chat_service
from utils.dependencies import get_current_user_or_guest

# Rate Limiter 초기화 (IP 주소 기반)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


class MessageRequest(BaseModel):
    """메시지 전송 요청"""
    session_id: str
    message: str
    user_id: Optional[int] = None  # 게스트 모드에서 사용
    
    @classmethod
    def validate_message(cls, v: str) -> str:
        """메시지 검증"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "message": "2024년 공과대학 졸업 요건 알려줘"
            }
        }


@router.post("/message")
@limiter.limit("30/minute")  # 1분에 30개 요청 제한
async def send_message(
    request: Request,  # SlowAPI가 요구하는 Request 객체
    message_request: MessageRequest,
    current_user: dict = Depends(get_current_user_or_guest),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    메시지 전송 및 응답
    
    Agent Engine에 메시지를 전송하고 전체 응답을 한 번에 반환합니다.
    인증 없이도 게스트로 메시지 전송 가능합니다.
    
    Headers (선택사항):
        Authorization: Bearer {access_token}
    
    Body:
        session_id: 세션 UUID
        message: 전송할 메시지
        user_id: 사용자 ID (게스트 모드에서 세션 생성 시 받은 ID)
    
    Response (JSON):
        {"text": "응답 텍스트", "done": true}
    """
    # 게스트 모드에서는 요청에서 user_id를 가져옴
    is_guest = current_user.get("is_guest", False)
    
    if is_guest and message_request.user_id:
        user_id = message_request.user_id
        print(f"[Chat] Guest message with user_id from request: {user_id}")
    else:
        user_id = current_user["id"]
    
    # session_id 검증
    try:
        session_uuid = UUID(message_request.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    try:
        # Agent Engine에서 스트리밍 응답을 모두 모으기
        full_response = ""
        async for text_chunk in chat_service.stream_message(
            user_id=user_id,
            session_sid=session_uuid,
            message_text=message_request.message
        ):
            full_response += text_chunk
        
        # 순수 텍스트만 반환
        return {"text": full_response}
        
    except Exception as e:
        # 에러 발생 시
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )
