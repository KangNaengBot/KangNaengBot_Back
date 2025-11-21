"""
세션 관련 라우터 모듈
"""
from fastapi import APIRouter
from .create_session import router as create_router
from .list_sessions import router as list_router
from .get_session_messages import router as get_messages_router
from .delete_session import router as delete_router

# 메인 라우터에 서브 라우터 통합
router = APIRouter(prefix="/sessions", tags=["sessions"])
router.include_router(create_router)
router.include_router(list_router)
router.include_router(get_messages_router)
router.include_router(delete_router)

__all__ = ['router']
