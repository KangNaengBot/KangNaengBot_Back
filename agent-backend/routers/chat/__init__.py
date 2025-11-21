"""
채팅 관련 라우터 모듈
"""
from fastapi import APIRouter
from .send_message import router as send_router

# 메인 라우터에 서브 라우터 통합
router = APIRouter(prefix="/chat", tags=["chat"])
router.include_router(send_router)

__all__ = ['router']
