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
        self.configuration = sib_api_v3_sdk.Configuration()
        self.configuration.api_key['api-key'] = config.BREVO_API_KEY
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
            print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
            return {"status": "error", "message": str(e)}


# 싱글톤처럼 사용하기 위해 인스턴스 생성
email_service = EmailService()

