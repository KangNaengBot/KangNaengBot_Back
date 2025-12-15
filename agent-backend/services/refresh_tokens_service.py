"""
RefreshTokensService - Refresh Token으로 새 토큰 생성 (Sliding Session)

단일 책임: Refresh Token을 검증하고 새로운 Access + Refresh Token을 발급합니다.
"""
from typing import Tuple
from utils.jwt import verify_refresh_token, create_access_token, create_refresh_token


class RefreshTokensService:
    """
    토큰 갱신 서비스
    
    Refresh Token을 검증하고 새 Access Token(1시간)과 
    새 Refresh Token(7일)을 발급합니다. (Sliding Session)
    """
    
    @staticmethod
    def refresh_tokens(refresh_token: str) -> Tuple[str, str]:
        """
        Refresh Token으로 새 토큰 발급
        
        Sliding Session 방식:
        - 사용할 때마다 새 Refresh Token 발급 (7일 연장)
        - 기존 Refresh Token은 자동으로 만료됨
        
        Args:
            refresh_token: 기존 Refresh Token
            
        Returns:
            (new_access_token, new_refresh_token) 튜플
            
        Raises:
            ValueError: Refresh Token이 무효하거나 만료된 경우
            
        Example:
            new_access, new_refresh = RefreshTokensService.refresh_tokens(old_refresh_token)
        """
        # Refresh Token 검증
        payload = verify_refresh_token(refresh_token)
        
        if not payload:
            raise ValueError("Invalid or expired refresh token")
        
        # user_id 추출
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Invalid refresh token: missing user_id")
        
        # 새 Access Token 생성 (1시간)
        # email은 Refresh Token에 없으므로 user_id만 포함
        new_access_token = create_access_token(data={
            "user_id": user_id
        })
        
        # 새 Refresh Token 생성 (7일) - Sliding Session
        new_refresh_token = create_refresh_token(user_id=user_id)
        
        print(f"[RefreshTokensService] Tokens refreshed for user_id={user_id}")
        
        return new_access_token, new_refresh_token


# Convenience function
def refresh_tokens(refresh_token: str) -> Tuple[str, str]:
    """토큰 갱신 (편의 함수)"""
    return RefreshTokensService.refresh_tokens(refresh_token)
