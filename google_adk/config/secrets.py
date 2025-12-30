import os
from google.cloud import secretmanager
import google.auth.exceptions

def get_secret(secret_id: str, default: str = None, version: str = "latest") -> str:
    """
    Secret Manager에서 시크릿 값을 가져옵니다.
    로컬 환경 변수가 있으면 우선 사용합니다 (오버라이드).
    
    Args:
        secret_id: Secret Manager의 시크릿 ID
        default: Secret Manager 접근 실패 시 반환할 기본값
        version: 시크릿 버전 ("latest" 또는 특정 버전 번호, 예: "2")
    """
    # 1. 환경 변수 우선 확인 (로컬 개발 편의성)
    if secret_id in os.environ:
        return os.environ[secret_id]

    # 2. Secret Manager 조회
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        print(f"[SecretManager] ✅ {secret_id} 버전 {version} 로드 성공")
        return secret_value
    except google.auth.exceptions.DefaultCredentialsError as e:
        print(f"[SecretManager] ⚠️ 인증 오류: Google Cloud 인증이 필요합니다.")
        print(f"[SecretManager] 다음 명령어를 실행하세요: gcloud auth application-default login")
        print(f"[SecretManager] 에러 상세: {e}")
        return default
    except Exception as e:
        # latest 버전이 실패하면 버전 2를 시도 (BREVO_API_KEY의 경우)
        if version == "latest" and "404" in str(e) or "not found" in str(e).lower():
            print(f"[SecretManager] ⚠️ latest 버전을 찾을 수 없어 버전 2를 시도합니다...")
            try:
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{project_id}/secrets/{secret_id}/versions/2"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                print(f"[SecretManager] ✅ {secret_id} 버전 2 로드 성공")
                return secret_value
            except Exception as e2:
                print(f"[SecretManager] ⚠️ 버전 2도 실패: {e2}")
        
        print(f"[SecretManager] ⚠️ Secret {secret_id} 접근 실패: {e}")
        return default
