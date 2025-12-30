"""
이메일 관련 라우터 모듈
"""
from fastapi import APIRouter
from .send_email import router as send_email_router

# 메인 라우터에 서브 라우터 통합
router = APIRouter(prefix="/email", tags=["email"])
router.include_router(send_email_router)

__all__ = ['router']

