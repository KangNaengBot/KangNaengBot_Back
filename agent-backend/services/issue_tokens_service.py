"""
IssueTokensService - Access Token + Refresh Token 발급

단일 책임: 사용자 정보를 받아 두 가지 토큰을 함께 발급합니다.
"""
from typing import Tuple


class IssueTokensService:
    """
    토큰 발급 서비스
    
    Access Token(1시간)과 Refresh Token(7일)을 함께 발급합니다.
    """
    
    @staticmethod
    def issue_tokens(user_id: int) -> Tuple[str, str]:
        """
        Access Token과 Refresh Token 발급
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            (access_token, refresh_token) 튜플
            
        Example:
            access_token, refresh_token = IssueTokensService.issue_tokens(123)
            
        Note:
            실제 토큰 생성은 utils/jwt.issue_token_pair()로 위임됩니다.
        """
        from utils.jwt import issue_token_pair
        
        print(f"[IssueTokensService] Tokens issued for user_id={user_id}")
        return issue_token_pair(user_id)


# Convenience function
def issue_tokens(user_id: int) -> Tuple[str, str]:
    """토큰 발급 (편의 함수)"""
    return IssueTokensService.issue_tokens(user_id)
