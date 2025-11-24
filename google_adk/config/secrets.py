import os
from google.cloud import secretmanager
import google.auth.exceptions

def get_secret(secret_id: str, default: str = None) -> str:
    """
    Secret Manager에서 시크릿 값을 가져옵니다.
    로컬 환경 변수가 있으면 우선 사용합니다 (오버라이드).
    """
    # 1. 환경 변수 우선 확인 (로컬 개발 편의성)
    if secret_id in os.environ:
        return os.environ[secret_id]

    # 2. Secret Manager 조회
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # 로컬에서 인증 정보가 없거나, 권한이 없거나, 시크릿이 없는 경우
        print(f"Warning: Could not access secret {secret_id}: {e}")
        return default
