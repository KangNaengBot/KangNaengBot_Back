from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

router = APIRouter(prefix="/proxy/subject", tags=["Subject Proxy"])

# 강남대학교 강의계획서 시스템 Base URL
BASE_URL = "https://app.kangnam.ac.kr/knumis/sbr"

# ==================================================================
# [Helper Functions]
# ==================================================================

def parse_syllabus_html(html: str) -> Dict[str, Any]:
    """강의계획서 상세 HTML을 파싱하여 JSON(dict) 형태로 반환합니다."""
    soup = BeautifulSoup(html, "html.parser")   
    data = {}

    # 메인 정보 테이블 파싱
    main_tbody = soup.find("tbody")
    if not main_tbody:
        main_tbody = soup

    def get_main_text(label):
        """<th> 레이블로 <td> 텍스트를 찾는 헬퍼"""
        th = main_tbody.find("th", string=lambda s: s and label in s.strip())
        if not th:
            return ""
        
        td = th.find_next_sibling("td")
        if td:
            for br in td.find_all("br"): 
                br.replace_with("\n")
            return td.get_text(strip=True)
        
        tr = th.find_parent("tr")
        if not tr: 
            return ""
        
        all_cells = tr.find_all(["th", "td"])
        found_th = False
        for cell in all_cells:
            if cell == th:
                found_th = True
                continue
            if found_th and cell.name == "td":
                for br in cell.find_all("br"): 
                    br.replace_with("\n")
                return cell.get_text(strip=True)
        return ""

    # 기본 정보 추출
    data["년도"] = get_main_text("년 도")
    data["학기"] = get_main_text("학 기")
    data["교과목명_한글"] = get_main_text("한글")
    data["교과목명_영문"] = get_main_text("영문")
    data["담당교수"] = get_main_text("담당교수")
    data["학수번호_분반"] = get_main_text("학수번호-분반")
    data["강의요일교시"] = get_main_text("강의요일교시")
    data["학점_시간수"] = get_main_text("학점")
    data["강의실"] = get_main_text("강의실")
    data["핵심역량"] = get_main_text("핵심역량")
    data["성적평가기준"] = get_main_text("성적평가기준")
    data["연구실"] = get_main_text("연구실")
    data["E-Mail"] = get_main_text("E-Mail")
    data["휴대전화"] = get_main_text("휴대전화")
    data["면담가능시간"] = get_main_text("면담가능시간")
    data["연구일"] = get_main_text("연구일")
    data["관리부서"] = get_main_text("관리부서")
    data["선수과목"] = get_main_text("선수과목")
    data["관련_기초과목"] = get_main_text("기초과목")
    data["동시수강_관련과목"] = get_main_text("동시수강")
    data["관련_고급과목"] = get_main_text("고급과목")
    data["교과목_개요"] = get_main_text("교과목")
    data["수업목표"] = get_main_text("수업목표")
    data["교수학습_세부운영_방법"] = get_main_text("세부운영")
    data["수업운영방식"] = get_main_text("수업운영방식")
    data["주교재"] = get_main_text("주교재")
    data["참고도서"] = get_main_text("참고도서")

    # 체크박스 항목 파싱
    def get_checked_labels(th_label_search):
        """특정 <th> 하위 <td>에서 체크된 항목 텍스트 추출"""
        th_label_search = th_label_search.replace("<br>", "\n").strip()
        th = main_tbody.find("th", string=lambda s: s and th_label_search in s.strip())
        if not th: 
            return []
        
        td = th.find_next_sibling("td", {"class": "displayOn"})
        if not td: 
            td = th.find_next_sibling("td")
        if not td: 
            return []
        
        checked_labels = []
        for checkbox in td.find_all("input", {"type": "checkbox", "checked": True}):
            label_node = checkbox.next_sibling
            label_text = ""
            while label_node:
                if isinstance(label_node, str):
                    label_text = label_node.string.strip()
                elif label_node.name:
                    label_text = label_node.get_text(strip=True)
                
                if label_text:
                    checked_labels.append(label_text)
                    break
                label_node = label_node.next_sibling
        return checked_labels

    data["이수구분_교양"] = get_checked_labels("교양")
    data["이수구분_전공"] = get_checked_labels("전공")
    data["이수구분_일반선택"] = get_checked_labels("일반선택")

    # 학부(과)
    td_dept = main_tbody.find("td", string=re.compile(r"학부\(과\) :"))
    if td_dept:
        data["학부(과)"] = td_dept.get_text(strip=True).split(":")[-1].strip()

    # 강좌특성
    th_feature = main_tbody.find("th", string=lambda s: s and "강좌특성" in s)
    checked_features = []
    if th_feature:
        td_feature = th_feature.find_next_sibling("td", {"class": "displayOn"})
        if not td_feature: 
            td_feature = th_feature.find_next_sibling("td")
        
        if td_feature:
            for checkbox in td_feature.find_all("input", {"type": "checkbox", "checked": True}):
                label_node = checkbox.next_sibling
                label_text = ""
                while label_node:
                    if isinstance(label_node, str):
                        label_text = label_node.string.strip()
                    elif label_node.name:
                        label_text = label_node.get_text(strip=True)
                    
                    if label_text:
                        checked_features.append(label_text)
                        break
                    label_node = label_node.next_sibling
    data["강좌특성"] = checked_features

    # 교수학습방법
    learning_methods = {}
    learning_methods["표준"] = get_checked_labels("표준 교과목운영 <br>기준")
    learning_methods["자기주도식"] = get_checked_labels("학생 자기주도식<br>수업운영")
    learning_methods["현장연계"] = get_checked_labels("현장 연계 방법")
    data["교수학습방법"] = learning_methods
    
    # 장애학생 지원
    data["장애학생_시험시간"] = get_checked_labels("시험시간<br>조정여부")
    data["장애학생_지원사항"] = get_checked_labels("지원사항")

    # 평가 방법
    eval_data = {}
    th_eval = main_tbody.find("th", string="평가방법")
    if th_eval:
        nested_table = th_eval.find_next("table")
        if nested_table:
            labels = []
            values = []
            
            for th in nested_table.find_all("th"):
                label = th.get_text(strip=True)
                if "과제/퀴즈" in label: 
                    desc_td = th.find_next_sibling("td")
                    if desc_td:
                        eval_data["세부사항"] = desc_td.get_text(strip=True)
                    break
                if label:
                    labels.append(label)
            
            for td in nested_table.find_all("td"):
                if "과제/퀴즈" in td.find_parent("tr").get_text(strip=True):
                    continue
                values.append(td.get_text(strip=True))
            
            eval_data["항목"] = dict(zip(labels, values[:len(labels)]))
    data["평가방법"] = eval_data

    # 주차별 강의 계획
    weekly_plan = []
    th_week_header = soup.find("th", string="주차")
    if th_week_header:
        table = th_week_header.find_parent("table")
        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 6: 
                        week_data = {
                            "주차": cols[0].get_text(strip=True),
                            "학습주제": cols[1].get_text(strip=True),
                            "수업방식/이용기재": cols[2].get_text(strip=True),
                            "교수학습자료": cols[3].get_text(strip=True),
                            "과제": cols[4].get_text(strip=True),
                            "수업운영방식": cols[5].get_text(strip=True)
                        }
                        weekly_plan.append(week_data)
    data["주차별강의계획"] = weekly_plan

    return data


def parse_course_list(html: str) -> List[Dict[str, str]]:
    """과목 목록 HTML을 파싱하여 과목 정보 리스트를 반환합니다."""
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    
    rows = soup.select("div#list table.grid_list tr[id^='row']")
    
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue

        onclick_attr = tds[7].find("div", onclick=True)
        if not onclick_attr:
            continue
            
        match = re.search(r"goPrint\([^,]+,'([^']+)'\)", str(onclick_attr))
        if not match:
            continue

        params_str = match.group(1)
        
        course_info = {
            "학수번호": tds[0].get_text(strip=True),
            "분반": tds[1].get_text(strip=True),
            "과목명": tds[2].get_text(strip=True),
            "담당교수": tds[3].get_text(strip=True),
            "학점": tds[4].get_text(strip=True),
            "시수": tds[5].get_text(strip=True),
            "강의시간": tds[6].get_text(strip=True),
            "params": params_str
        }
        courses.append(course_info)
        
    return courses

# ==================================================================
# [API Endpoints]
# ==================================================================

class SearchRequest(BaseModel):
    keyword: str
    year: Optional[str] = None
    semester: Optional[str] = None

class DetailRequest(BaseModel):
    params: str

@router.post("/search")
async def search_subject(request: SearchRequest):
    """과목 목록 검색 프록시"""
    keyword = request.keyword
    year = request.year
    semester = request.semester
    
    # 기본값 설정
    if year is None:
        year = str(datetime.now().year)
    
    if semester is None:
        current_month = datetime.now().month
        if 3 <= current_month <= 7:
            semester = "1"
        else:
            semester = "2"
            
    try:
        # 세션 생성
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # 1. 쿠키 확보
        form_page_url = f"{BASE_URL}/sbr1010.jsp"
        try:
            session.get(form_page_url, timeout=10)
        except requests.RequestException as e:
            print(f"Warning: 세션 쿠키 확보 실패 가능성: {e}")
        
        # 2. POST 페이로드
        payload = {
            "empl_numb": "",
            "schl_year": year,
            "schl_smst": semester,
            "subj_numb": "",
            "lctr_clas": "",
            "save_gubn": "",
            "dept_srch": "",
            "srch_gubn": "11",
            "subj_knam": keyword,
            "subj_knam2": "",
            "dept_code1": "",
            "grad_area1": "H1"
        }
        
        # 3. EUC-KR 인코딩
        payload_encoded = {}
        for key, value in payload.items():
            payload_encoded[key] = value.encode('euc-kr')
        
        # 4. POST 요청
        post_url = f"{BASE_URL}/sbr1010L.jsp"
        headers = {
            "Referer": form_page_url,
            "Origin": "https://app.kangnam.ac.kr",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        r_post = session.post(post_url, data=payload_encoded, headers=headers, timeout=15)
        r_post.raise_for_status()
        r_post.encoding = 'euc-kr'
        
        # 5. 파싱
        courses = parse_course_list(r_post.text)
        
        return {
            "status": "success",
            "count": len(courses),
            "courses": courses,
            "search_params": {
                "keyword": keyword,
                "year": year,
                "semester": semester
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detail")
async def get_subject_detail(request: DetailRequest):
    """강의계획서 상세 조회 프록시"""
    params_str = request.params
    
    try:
        # 세션 생성
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # params 파싱
        val = params_str.split(',')
        empl_numb = val[0]
        schl_year = val[1]
        schl_smst = val[2]
        subj_numb = val[3]
        lctr_clas = val[4]
        
        # URL 결정
        temp_year = int(schl_year)
        if temp_year >= 2020:
            url_path = 'syllabus2020.jsp'
        elif temp_year >= 2017:
            url_path = 'syllabus2017.jsp'
        else:
            url_path = 'syllabus.jsp'
        
        repo_path = '../sbr/sbr3070_New.mrd' if temp_year >= 2014 else '../sbr/sbr3070.mrd'
        
        syllabus_url = (
            f"{BASE_URL}/{url_path}?schl_year={schl_year}&schl_smst={schl_smst}"
            f"&subj_numb={subj_numb}&lctr_clas={lctr_clas}&empl_numb={empl_numb}"
            f"&repo_path={repo_path}&winopt=1010"
        )
        
        # 강의계획서 요청
        r_syllabus = session.get(syllabus_url, timeout=15)
        r_syllabus.raise_for_status()
        r_syllabus.encoding = 'euc-kr'
        
        # 파싱
        syllabus_data = parse_syllabus_html(r_syllabus.text)
        
        return {
            "status": "success",
            "syllabus": syllabus_data,
            "syllabus_url": syllabus_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
