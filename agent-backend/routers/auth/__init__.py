"""
Auth 라우터 모듈
"""
from fastapi import APIRouter
from .google_login import router as login_router
from .google_callback import router as callback_router
from .get_me import router as get_me_router
from .generate_token import router as generate_token_router

# 메인 라우터에 서브 라우터 통합
router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(login_router)
router.include_router(callback_router)
router.include_router(get_me_router)
router.include_router(generate_token_router)

__all__ = ['router']
