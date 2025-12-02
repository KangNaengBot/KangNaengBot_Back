"""
강남대학교 과목 정보 검색 도구 (Vertex AI Search 기반)
"""

import json
from google.adk.tools import FunctionTool
from google.auth import default
from google.auth.transport.requests import Request
from typing import Dict, Any, Optional

# Vertex AI Search 엔진 endpoint
VERTEX_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-subject-info_1764222007906/"
    "servingConfigs/default_search:search"
)

# 공통 함수: Vertex AI Search API 호출
def vertex_ai_search_request(query: str, page_size: int = 10, offset: int = 0) -> Dict[str, Any]:
    """
    Vertex AI Search API를 curl 호출 형태로 실행하고 결과를 반환.
    """
    try:
        # Google Auth 라이브러리로 access token 가져오기 (배포 환경 호환)
        credentials, project = default()
        if not credentials.valid:
            credentials.refresh(Request())
        token = credentials.token
        
        payload = {
            "query": query,
            "pageSize": page_size,
            "offset": offset,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "languageCode": "ko",
            "userInfo": {"timeZone": "Asia/Seoul"}
        }
        
        # API 호출
        import requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(VERTEX_SEARCH_ENDPOINT, headers=headers, json=payload)
        result = response.json()
        
        # 정리된 형태로 반환
        if "results" in result:
            formatted_results = []
            for i, item in enumerate(result["results"], start=1 + offset):
                doc = item.get("document", {})
                structured = doc.get("structData", {})
                
                # 메타데이터와 콘텐츠 병합
                content = structured.get("content", "")
                metadata = structured.get("metadata", {})
                
                formatted_results.append({
                    "rank": i,
                    "title": doc.get("id"), # 학수번호-분반
                    "content": content,
                    "metadata": metadata,
                    "snippet": item.get("snippet", "")
                })
            
            return {
                "status": "success",
                "count": len(formatted_results),
                "total_size": result.get("totalSize", 0),
                "query": query,
                "offset": offset,
                "results": formatted_results,
                "message": f"'{query}'에 대한 검색 결과 {len(formatted_results)}개를 찾았습니다. (전체 {result.get('totalSize', '?')}개 중 {offset+1}~{offset+len(formatted_results)})"
            }
        else:
            return {
                "status": "error",
                "query": query,
                "message": "검색 결과가 없습니다.",
                "raw_response": result
            }
        
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "message": str(e)
        }

def search_subject_info(query: str, offset: int = 0) -> Dict[str, Any]:
    """
    강남대학교 과목 정보를 자유롭게 검색합니다.
    예: "소프트웨어공학 수업 알려줘", "김철수 교수님 수업", "3학년 전공 수업"
    
    Args:
        query: 검색어
        offset: 검색 결과 시작 위치 (기본값 0). 더 많은 결과를 볼 때 10, 20 등으로 설정하세요.
    """
    return vertex_ai_search_request(query, offset=offset)

def search_subject_by_grade_and_dept(grade: int, department: str, offset: int = 0) -> Dict[str, Any]:
    """
    특정 학과와 학년의 수업을 검색합니다.
    예: 3학년 소프트웨어전공 수업
    
    Args:
        grade: 학년 (1~4)
        department: 학과/전공 명
        offset: 검색 결과 시작 위치 (기본값 0). 더 많은 결과를 볼 때 10, 20 등으로 설정하세요.
    """
    query = f"{department} {grade}학년 수업"
    return vertex_ai_search_request(query, offset=offset)

def search_subject_syllabus(subject_name: str, offset: int = 0) -> Dict[str, Any]:
    """
    특정 과목의 강의계획서를 검색합니다.
    
    Args:
        subject_name: 과목명
        offset: 검색 결과 시작 위치 (기본값 0).
    """
    query = f"{subject_name} 강의계획서"
    return vertex_ai_search_request(query, offset=offset)


search_subject_info_tool = FunctionTool(search_subject_info)
search_subject_by_grade_and_dept_tool = FunctionTool(search_subject_by_grade_and_dept)
search_subject_syllabus_tool = FunctionTool(search_subject_syllabus)

ALL_SUBJECT_TOOLS = [
    search_subject_info_tool,
    search_subject_by_grade_and_dept_tool,
    search_subject_syllabus_tool
]
