"""
입력 살균(Input Sanitization) 유틸리티

XSS, SQL Injection, Script Injection 등 다양한 공격으로부터 입력을 보호합니다.
모든 서비스 레이어에서 사용자 입력을 받을 때 최우선으로 적용되어야 합니다.
"""
import re
import html
from typing import Optional


class InputSanitizer:
    """
    입력 살균 클래스
    
    다층 방어 전략:
    1. HTML/Script 태그 제거 및 이스케이핑
    2. 위험한 문자 패턴 제거
    3. 최대 길이 제한
    4. SQL Injection 패턴 탐지
    """
    
    # 위험한 HTML/Script 패턴
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # <script> 태그
        r'<iframe[^>]*>.*?</iframe>',  # <iframe> 태그
        r'javascript:',                 # javascript: 프로토콜
        r'on\w+\s*=',                  # onclick, onload 등
        r'<object[^>]*>.*?</object>',  # <object> 태그
        r'<embed[^>]*>',               # <embed> 태그
        r'<applet[^>]*>.*?</applet>',  # <applet> 태그
        r'<meta[^>]*>',                # <meta> 태그
        r'<link[^>]*>',                # <link> 태그
        r'vbscript:',                  # vbscript: 프로토콜
        r'data:text/html',             # data URI
    ]
    
    # SQL Injection 의심 패턴 (경고용)
    SQL_INJECTION_PATTERNS = [
        r"(\bOR\b|\bAND\b).*=.*",      # OR 1=1, AND 1=1
        r"';?\s*(DROP|DELETE|INSERT|UPDATE|SELECT)\s",  # SQL 명령어
        r"--",                         # SQL 주석
        r"/\*.*\*/",                   # 블록 주석
        r"UNION\s+SELECT",             # UNION SELECT
        r"exec\s*\(",                  # exec(
    ]
    
    @classmethod
    def sanitize_text(
        cls,
        text: str,
        max_length: Optional[int] = None,
        strip_html: bool = True,
        allow_newlines: bool = True
    ) -> str:
        """
        텍스트 입력 살균
        
        Args:
            text: 살균할 텍스트
            max_length: 최대 길이 (None이면 제한 없음, 기본값: 제한 없음)
            strip_html: HTML 태그 제거 여부
            allow_newlines: 줄바꿈 허용 여부
            
        Returns:
            살균된 텍스트
            
        Raises:
            ValueError: 위험한 패턴이 감지된 경우
        """
        if not text or not isinstance(text, str):
            return ""
        
        original_text = text
        
        # 1. 최대 길이 제한
        if max_length and len(text) > max_length:
            text = text[:max_length]
            print(f"[Sanitizer] Text truncated: {len(original_text)} -> {max_length}")
        
        # 2. 위험한 패턴 탐지 및 제거
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[Sanitizer] ⚠️ Dangerous pattern detected: {pattern}")
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 3. SQL Injection 패턴 탐지 (경고만, 제거하지 않음 - 오탐 가능성)
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[Sanitizer] ⚠️ Possible SQL injection pattern detected: {pattern}")
                # SQL Injection은 ORM(SQLAlchemy)이 방어하므로 경고만 출력
        
        # 4. HTML 이스케이핑 (선택적)
        if strip_html:
            # HTML 특수문자를 안전한 엔티티로 변환
            text = html.escape(text)
        
        # 5. 줄바꿈 처리
        if not allow_newlines:
            text = text.replace('\n', ' ').replace('\r', ' ')
        
        # 6. 앞뒤 공백 제거
        text = text.strip()
        
        # 변경사항 로깅
        if text != original_text:
            print(f"[Sanitizer] Input sanitized: {len(original_text)} -> {len(text)} chars")
        
        return text
    
    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """
        채팅 메시지 전용 살균
        
        채팅 메시지는 HTML을 제거하되, 줄바꿈은 허용합니다.
        
        Args:
            message: 채팅 메시지
            
        Returns:
            살균된 메시지
        """
        return cls.sanitize_text(
            message,
            max_length=None,       # 길이 제한 없음
            strip_html=True,       # HTML 태그 제거
            allow_newlines=True    # 줄바꿈 허용
        )
    
    @classmethod
    def sanitize_title(cls, title: str) -> str:
        """
        제목/타이틀 전용 살균
        
        Args:
            title: 제목
            
        Returns:
            살균된 제목
        """
        return cls.sanitize_text(
            title,
            max_length=None,       # 길이 제한 없음
            strip_html=True,       # HTML 태그 제거
            allow_newlines=False   # 줄바꿈 불허용
        )
    
    @classmethod
    def sanitize_user_info(cls, info: str) -> str:
        """
        사용자 정보(이름, 학번 등) 전용 살균
        
        Args:
            info: 사용자 정보
            
        Returns:
            살균된 정보
        """
        return cls.sanitize_text(
            info,
            max_length=None,       # 길이 제한 없음
            strip_html=True,       # HTML 태그 제거
            allow_newlines=False   # 줄바꿈 불허용
        )
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """
        UUID 형식 검증
        
        Args:
            uuid_str: UUID 문자열
            
        Returns:
            유효하면 True
        """
        uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        return bool(re.match(uuid_pattern, uuid_str.lower()))
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        이메일 형식 검증
        
        Args:
            email: 이메일 주소
            
        Returns:
            유효하면 True
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))


# 편의 함수들
def sanitize_message(message: str) -> str:
    """채팅 메시지 살균 (편의 함수)"""
    return InputSanitizer.sanitize_message(message)


def sanitize_title(title: str) -> str:
    """제목 살균 (편의 함수)"""
    return InputSanitizer.sanitize_title(title)


def sanitize_user_info(info: str) -> str:
    """사용자 정보 살균 (편의 함수)"""
    return InputSanitizer.sanitize_user_info(info)
