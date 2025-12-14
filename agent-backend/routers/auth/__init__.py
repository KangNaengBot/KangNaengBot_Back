"""
인증 관련 라우터
"""
from fastapi import APIRouter

from .google_login import router as google_login_router
from .google_callback import router as google_callback_router
from .get_me import router as get_me_router
from .generate_token import router as generate_token_router
from .refresh_token import router as refresh_token_router
from .logout import router as logout_router

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(google_login_router)
router.include_router(google_callback_router)
router.include_router(get_me_router)
router.include_router(generate_token_router)
router.include_router(refresh_token_router)  # POST /auth/refresh
router.include_router(logout_router)         # POST /auth/logout

__all__ = ['router']
