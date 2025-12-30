"""
Brevo 이메일 서비스

Brevo API를 사용하여 이메일을 전송하는 서비스
"""
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import List
import config


class EmailService:
    """Brevo를 사용한 이메일 전송 서비스"""

    def __init__(self):
        # Brevo 설정 초기화
        if not config.BREVO_API_KEY:
            raise ValueError(
                "BREVO_API_KEY가 설정되지 않았습니다. "
                "환경 변수 BREVO_API_KEY를 설정하거나 Secret Manager에 저장하세요."
            )
        
        api_key = config.BREVO_API_KEY.strip() if config.BREVO_API_KEY else None
        if not api_key:
            raise ValueError("BREVO_API_KEY가 비어있습니다.")
        
        # API 키 디버깅 (처음 10자만 표시)
        api_key_preview = api_key[:10] + "..." if len(api_key) > 10 else api_key
        print(f"[EmailService] BREVO_API_KEY 로드됨: {api_key_preview}")
        
        self.configuration = sib_api_v3_sdk.Configuration()
        self.configuration.api_key['api-key'] = api_key
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(self.configuration)
        )

    def send_bulk_emails(self, recipients: List[str], subject: str, content: str) -> dict:
        """
        다수의 수신자에게 이메일을 전송합니다.

        :param recipients: 이메일 주소 리스트 (['a@a.com', 'b@b.com'])
        :param subject: 이메일 제목
        :param content: 이메일 내용 (HTML 가능)
        :return: 전송 결과 딕셔너리
        """
        # 1. Brevo 포맷에 맞게 수신자 리스트 변환
        # [{'email': 'user1@example.com'}, {'email': 'user2@example.com'}] 형태
        to_list = [{"email": email} for email in recipients]

        # 2. 이메일 데이터 구성
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to_list,
            sender={"name": config.SENDER_NAME, "email": config.SENDER_EMAIL},
            subject=subject,
            html_content=content
        )

        try:
            # 3. API 호출
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            return {"status": "success", "message_id": api_response.message_id}

        except ApiException as e:
            error_msg = str(e)
            print(f"[EmailService] Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
            
            # 401 Unauthorized 에러인 경우 더 자세한 정보 제공
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                print(f"[EmailService] ⚠️ API 키 인증 실패!")
                print(f"[EmailService] 현재 API 키: {config.BREVO_API_KEY[:10] if config.BREVO_API_KEY else 'None'}...")
                print(f"[EmailService] 환경 변수 BREVO_API_KEY 확인 필요")
            
            return {"status": "error", "message": error_msg}


# 싱글톤 패턴 - Lazy initialization
_email_service_instance = None

def get_email_service() -> EmailService:
    """EmailService 싱글톤 인스턴스를 반환합니다 (Lazy initialization)"""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance

# 기존 코드와의 호환성을 위해 email_service 변수도 제공
# 하지만 실제로는 함수 호출 시점에 초기화됨
class EmailServiceProxy:
    """EmailService의 프록시 클래스 - 실제 사용 시점에 초기화"""
    def __getattr__(self, name):
        return getattr(get_email_service(), name)

email_service = EmailServiceProxy()

