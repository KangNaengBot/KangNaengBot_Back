"""
POST /email/send - 단체 이메일 전송
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List
from services.email_service import email_service

router = APIRouter()


# 요청 바디 모델 정의 (DTO)
class EmailRequest(BaseModel):
    """이메일 전송 요청 모델"""
    recipients: List[EmailStr]  # 이메일 리스트 (1명이어도 리스트로 받음)
    subject: str
    content: str


@router.post("/send", summary="단체 이메일 전송")
async def send_email(request: EmailRequest):
    """
    프론트엔드로부터 이메일 리스트, 제목, 내용을 받아 단체 메일을 전송합니다.
    
    Request Body:
        recipients: 이메일 주소 리스트 (예: ["user1@example.com", "user2@example.com"])
        subject: 이메일 제목
        content: 이메일 내용 (HTML 가능)
    
    Returns:
        전송 성공 메시지 및 수신자 수
    """
    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수신자 이메일 목록이 비어있습니다."
        )

    # 서비스 호출
    result = email_service.send_bulk_emails(
        recipients=request.recipients,
        subject=request.subject,
        content=request.content
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이메일 전송 실패: {result['message']}"
        )

    return {
        "message": "이메일 전송 요청이 성공했습니다.",
        "recipient_count": len(request.recipients),
        "data": result
    }

