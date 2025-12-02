"""
강남대학교 과목 정보 Vertex AI Search 업로드 스크립트

사용법:
    python google_adk/data/과목정보/upload_subjects.py
"""

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine
from google.cloud import storage
from google.api_core.exceptions import AlreadyExists
import os

# ==============================
# 설정
# ==============================
PROJECT_ID = "kangnam-backend"
LOCATION = "global"
DATA_STORE_ID = "kangnam-subjects-datastore"
BUCKET_NAME = "kangnam-univ"
GCS_FOLDER = "rag_data/subjects"
LOCAL_FILE = "google_adk/data/과목정보/kangnam_all_2025_2.jsonl"

# GCS 입력 URI
GCS_URI = f"gs://{BUCKET_NAME}/{GCS_FOLDER}/{os.path.basename(LOCAL_FILE)}"

def create_data_store():
    """데이터 스토어 생성 (없으면)"""
    print("=" * 60)
    print("🔍 데이터 스토어 확인 및 생성")
    print("=" * 60)
    
    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global" else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    parent = client.collection_path(
        project=PROJECT_ID,
        location=LOCATION,
        collection="default_collection",
    )

    data_store = discoveryengine.DataStore(
        display_name="강남대학교 과목 정보 (2025-2)",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.NO_CONTENT,
    )

    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=DATA_STORE_ID,
        data_store=data_store,
    )

    try:
        operation = client.create_data_store(request=request)
        print(f"🚀 데이터 스토어 생성 요청 중... (ID: {DATA_STORE_ID})")
        response = operation.result(timeout=600)
        print("✅ 데이터 스토어 생성 완료!")
    except AlreadyExists:
        print(f"ℹ️ 데이터 스토어 '{DATA_STORE_ID}'가 이미 존재합니다. 생성을 건너뜁니다.")
    except Exception as e:
        print(f"❌ 데이터 스토어 생성 실패: {e}")
        raise

def upload_to_gcs():
    """JSONL 파일을 GCS에 업로드"""
    print("\n" + "=" * 60)
    print("📤 GCS 업로드 시작")
    print("=" * 60)
    
    if not os.path.exists(LOCAL_FILE):
        raise FileNotFoundError(f"로컬 파일을 찾을 수 없습니다: {LOCAL_FILE}")

    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    blob_name = f"{GCS_FOLDER}/{os.path.basename(LOCAL_FILE)}"
    blob = bucket.blob(blob_name)
    
    print(f"📁 로컬 파일: {LOCAL_FILE}")
    print(f"☁️  GCS 경로: gs://{BUCKET_NAME}/{blob_name}")
    
    blob.upload_from_filename(LOCAL_FILE)
    print("✅ GCS 업로드 완료!")

def import_documents():
    """Vertex AI Search에 문서 가져오기"""
    print("\n" + "=" * 60)
    print("📥 Vertex AI Search - 문서 Import 시작")
    print("=" * 60)
    
    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global" else None
    )
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    parent = client.branch_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATA_STORE_ID,
        branch="default_branch",
    )

    gcs_source = discoveryengine.GcsSource(
        input_uris=[GCS_URI],
        data_schema="custom",
    )

    import_request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
        auto_generate_ids=False,
        id_field="id",
    )

    print("🚀 문서 가져오기 요청 중...")
    operation = client.import_documents(request=import_request)
    print(f"🕐 작업 ID: {operation.operation.name}")
    print("⏳ 데이터 처리 중... (약 1~3분 소요)")

    try:
        result = operation.result(timeout=600)
        print("\n✅ 데이터 가져오기 완료!")
        print(f"성공적으로 처리된 문서 수: {result.import_sample.success_count}")
        if result.import_sample.failure_count > 0:
            print(f"⚠️ 실패한 문서 수: {result.import_sample.failure_count}")
            print(f"실패 샘플: {result.import_sample.failures}")
    except Exception as e:
        print(f"\n❌ 데이터 가져오기 실패: {e}")

if __name__ == "__main__":
    try:
        create_data_store()
        upload_to_gcs()
        import_documents()
        
        print("\n" + "=" * 60)
        print("🎉 모든 작업 완료!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 작업 중 오류 발생: {e}")
