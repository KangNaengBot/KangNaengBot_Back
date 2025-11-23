"""
POST /chat/message - 메시지 전송 및 스트리밍 응답
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import UUID
import json

from services.chat_service import ChatService, get_chat_service
from utils.dependencies import get_current_user

router = APIRouter()


class MessageRequest(BaseModel):
    """메시지 전송 요청"""
    session_id: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "message": "2024년 공과대학 졸업 요건 알려줘"
            }
        }


@router.post("/message")
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    메시지 전송 및 스트리밍 응답
    
    Agent Engine에 메시지를 전송하고 SSE(Server-Sent Events) 방식으로
    스트리밍 응답을 반환합니다.
    
    Headers:
        Authorization: Bearer {access_token}
    
    Body:
        session_id: 세션 UUID
        message: 전송할 메시지
    
    Response (SSE):
        data: {"text": "응답 텍스트", "done": false}
        data: {"text": "", "done": true}
    """
    user_id = current_user["id"]
    
    # session_id 검증
    try:
        session_uuid = UUID(request.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    async def event_generator():
        """SSE 이벤트 생성기"""
        try:
            # Agent Engine에서 스트리밍 응답 받기
            async for text_chunk in chat_service.stream_message(
                user_id=user_id,
                session_sid=session_uuid,
                message_text=request.message
            ):
                # SSE 포맷으로 전송
                event_data = {
                    "text": text_chunk,
                    "done": False
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 스트림 종료 신호
            yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"
        
        except Exception as e:
            # 에러 발생 시
            error_data = {
                "text": f"\n\n[오류] {str(e)}",
                "done": True,
                "error": True
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        }
    )
