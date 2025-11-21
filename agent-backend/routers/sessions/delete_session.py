"""
DELETE /sessions/{session_id} - 세션 삭제 (비활성화)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID

from services.session_service import SessionService, get_session_service
from utils.dependencies import get_current_user

router = APIRouter()


class DeleteSessionResponse(BaseModel):
    """세션 삭제 응답"""
    message: str


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    세션 비활성화 (소프트 삭제)
    
    Headers:
        Authorization: Bearer {access_token}
    
    Path Parameters:
        session_id: 세션 UUID
    
    Returns:
        message: 성공 메시지
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
    
    # 비활성화
    success = session_service.deactivate_session(session_uuid)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    
    return DeleteSessionResponse(
        message="Session deleted successfully"
    )
