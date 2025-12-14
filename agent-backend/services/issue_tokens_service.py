"""
IssueTokensService - Access Token + Refresh Token 발급

단일 책임: 사용자 정보를 받아 두 가지 토큰을 함께 발급합니다.
"""
from typing import Tuple
from utils.jwt import create_access_token, create_refresh_token


class IssueTokensService:
    """
    토큰 발급 서비스
    
    Access Token(1시간)과 Refresh Token(7일)을 함께 발급합니다.
    """
    
    @staticmethod
    def issue_tokens(user_id: int, email: str) -> Tuple[str, str]:
        """
        Access Token과 Refresh Token 발급
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            
        Returns:
            (access_token, refresh_token) 튜플
            
        Example:
            access_token, refresh_token = IssueTokensService.issue_tokens(123, "user@example.com")
        """
        # Access Token 생성 (1시간, type: "access")
        access_token = create_access_token(data={
            "user_id": user_id,
            "email": email
        })
        
        # Refresh Token 생성 (7일, type: "refresh")
        refresh_token = create_refresh_token(user_id=user_id)
        
        print(f"[IssueTokensService] Tokens issued for user_id={user_id}")
        
        return access_token, refresh_token


# Convenience function
def issue_tokens(user_id: int, email: str) -> Tuple[str, str]:
    """토큰 발급 (편의 함수)"""
    return IssueTokensService.issue_tokens(user_id, email)
