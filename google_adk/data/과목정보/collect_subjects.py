import requests
import re
import json
import time
import socket
import os
import requests.packages.urllib3.util.connection as urllib3_cn
from bs4 import BeautifulSoup
from urllib.parse import quote

# ----------------------------------------
# 0. 네트워크 설정 (IPv4 강제)
# ----------------------------------------
def allowed_gai_family():
    return socket.AF_INET

urllib3_cn.allowed_gai_family = allowed_gai_family

# ----------------------------------------
# 기본 설정
# ----------------------------------------
BASE_URL = "https://app.kangnam.ac.kr/knumis/sbr"
YEAR = "2025"
SEMESTER = "2"
OUTPUT_FILE = os.path.abspath(f"kangnam_all_{YEAR}_{SEMESTER}.jsonl")


# ----------------------------------------
# 1. 학부/전공 목록 (사용자 제공 데이터 하드코딩)
# ----------------------------------------
def fetch_departments():
    html = """
    <option value="5444">	ICT융합공학부 (공과대학)</option>
    <option value="5292">	Wel-Tech융합전공 (복지융합대학)</option>
    <option value="5447">	가상현실전공 (ICT융합공학부)</option>
    <option value="5335">	건축공학전공 (부동산건설학부)</option>
    <option value="5284">	경영학전공 (글로벌경영학부)</option>
    <option value="5285">	경영학전공(야) (글로벌경영학부(야))</option>
    <option value="5314">	경제금융전공 (정경학부)</option>
    <option value="5318">	경제금융전공(야) (정경학부(야))</option>
    <option value="5316">	공공인재학전공 (정경학부)</option>
    <option value="5320">	공공인재학전공(야) (정경학부(야))</option>
    <option value="5185">	교양 (대학)</option>
    <option value="5186">	교양(야) (교양)</option>
    <option value="5036">	교육학과 (사범대학)</option>
    <option value="5493">	국제지역학과 </option>
    <option value="5325">	국제지역학전공 (글로벌문화학부)</option>
    <option value="5257">	국제통상학전공 (글로벌경영학부)</option>
    <option value="5256">	글로벌경영학부 (경영관리대학)</option>
    <option value="5275">	글로벌경영학부(야) (경영관리대학)</option>
    <option value="5467">	글로벌문화콘텐츠대학 (대학)</option>
    <option value="5323">	글로벌문화학부 (글로벌인재대학)</option>
    <option value="5495">	기독교커뮤니케이션학과 </option>
    <option value="5261">	기독교학과 (글로벌인재대학)</option>
    <option value="5458">	기독교학전공 (글로벌문화학부)</option>
    <option value="5450">	데이터사이언스전공 (인공지능융합공학부)</option>
    <option value="5274">	도시건축융합공학전공 (부동산건설학부)</option>
    <option value="5480">	디자인학과 </option>
    <option value="5464">	문화콘텐츠전공 (글로벌문화학부)</option>
    <option value="5492">	문화콘텐츠학과 </option>
    <option value="5460">	반도체시스템융합전공 </option>
    <option value="5472">	법행정세무학부 (경영관리대학)</option>
    <option value="5473">	법행정세무학부(야) (경영관리대학)</option>
    <option value="5246">	복지융합대학 (대학)</option>
    <option value="5273">	부동산건설학부 (ICT건설공과대학)</option>
    <option value="5050">	부동산학전공 (ICT건설공과대학&gt;부동산건설학부)</option>
    <option value="5064">	사회복지학부 (복지융합대학)</option>
    <option value="5071">	사회복지학부(야) (복지융합대학)</option>
    <option value="5066">	사회사업학전공 (사회복지학부)</option>
    <option value="5073">	사회사업학전공(야) (사회복지학부(야))</option>
    <option value="5250">	사회서비스정책학전공 (사회복지학부)</option>
    <option value="5449">	산업경영공학전공 (인공지능융합공학부)</option>
    <option value="5459">	산업공학전공 (인공지능융합공학부)</option>
    <option value="5470">	상경학부 (경영관리대학)</option>
    <option value="5471">	상경학부(야) (경영관리대학)</option>
    <option value="5315">	세무학전공 (정경학부)</option>
    <option value="5319">	세무학전공(야) (정경학부(야))</option>
    <option value="5446">	소프트웨어전공 (ICT융합공학부)</option>
    <option value="5452">	스마트도시공학전공 (부동산건설학부)</option>
    <option value="5312">	스포츠복지전공 (예체능학부)</option>
    <option value="5457">	스포츠복지학과 (복지융합대학)</option>
    <option value="5479">	시니어비즈니스학과 </option>
    <option value="5251">	실버산업학과 (복지융합대학)</option>
    <option value="5311">	유니버설아트디자인전공 (예체능학부)</option>
    <option value="5456">	유니버설아트디자인학과 (복지융합대학)</option>
    <option value="5039">	유아교육과 (사범대학)</option>
    <option value="5157">	음악학과 (복지융합대학)</option>
    <option value="5310">	음악학전공 (예체능학부)</option>
    <option value="5445">	인공지능융합공학부 (공과대학)</option>
    <option value="5451">	인공지능전공 (인공지능융합공학부)</option>
    <option value="5468">	자유전공학부 (부총장직속)</option>
    <option value="5448">	전자공학전공 (ICT융합공학부)</option>
    <option value="5475">	전자반도체공학부 (공과대학)</option>
    <option value="5313">	정경학부 (경영관리대학)</option>
    <option value="5317">	정경학부(야) (경영관리대학)</option>
    <option value="5326">	중국지역학전공 (글로벌문화학부)</option>
    <option value="5494">	중국콘텐츠비즈니스학과 </option>
    <option value="5214">	중등특수교육과 (사범대학)</option>
    <option value="5481">	체육학과 </option>
    <option value="5213">	초등특수교육과 (사범대학)</option>
    <option value="5474">	컴퓨터공학부 (공과대학)</option>
    <option value="5324">	한영문화콘텐츠전공 (글로벌문화학부)</option>
    """
    soup = BeautifulSoup(html, "html.parser")
    departments = []
    for opt in soup.find_all("option"):
        code = opt.get("value", "").strip()
        name = opt.get_text(strip=True)
        if code and code != "----":
            departments.append({"code": code, "name": name})
    return departments


# ----------------------------------------
# 2. HTML에서 과목 목록 파싱
# ----------------------------------------
def parse_course_list(html: str):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div#list table.grid_list tr[id^='row']")
    result = []

    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue

        onclick_div = tds[7].find("div", onclick=True)
        if not onclick_div:
            continue

        match = re.search(r"goPrint\([^,]+,'([^']+)'\)", str(onclick_div))
        if not match:
            continue

        params = match.group(1)

        result.append({
            "학수번호": tds[0].get_text(strip=True),
            "분반": tds[1].get_text(strip=True),
            "과목명": tds[2].get_text(strip=True),
            "담당교수": tds[3].get_text(strip=True),
            "학점": tds[4].get_text(strip=True),
            "시수": tds[5].get_text(strip=True),
            "강의시간": tds[6].get_text(strip=True),
            "params": params
        })

    return result


# ----------------------------------------
# 3. 전공(H) / 교양(G) 과목 조회 API 호출
# ----------------------------------------
def fetch_courses_by_major(mode_code: str, grad_code: str):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        session.get(f"{BASE_URL}/sbr1010.jsp", timeout=10)

        payload = {
            "schl_year": YEAR,
            "schl_smst": SEMESTER,
            "dept_srch": mode_code,
            "srch_gubn": "21",
            "subj_knam": "",
            "subj_knam2": "",
            "dept_code1": mode_code,
            "grad_area1": grad_code
        }

        payload_encoded = {}
        for k, v in payload.items():
            payload_encoded[k] = v.encode("euc-kr")
            
        post_url = f"{BASE_URL}/sbr1010L.jsp"

        res = session.post(
            post_url,
            data=payload_encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )

        res.encoding = "euc-kr"
        return parse_course_list(res.text)
    except Exception as e:
        print(f"Error fetching courses for {mode_code}/{grad_code}: {e}")
        return []


# ----------------------------------------
# 4. 강의계획서 URL 생성
# ----------------------------------------
def construct_syllabus_url(params_str: str):
    try:
        val = params_str.split(',')
        empl_numb = val[0]
        schl_year = val[1]
        schl_smst = val[2]
        subj_numb = val[3]
        lctr_clas = val[4]

        year = int(schl_year)
        if year >= 2020:
            jsp = "syllabus2020.jsp"
        elif year >= 2017:
            jsp = "syllabus2017.jsp"
        else:
            jsp = "syllabus.jsp"

        repo = "../sbr/sbr3070_New.mrd" if year >= 2014 else "../sbr/sbr3070.mrd"

        return (
            f"{BASE_URL}/{jsp}"
            f"?schl_year={schl_year}&schl_smst={schl_smst}"
            f"&subj_numb={subj_numb}&lctr_clas={lctr_clas}&empl_numb={empl_numb}"
            f"&repo_path={repo}&winopt=1010"
        )
    except:
        return ""


# ----------------------------------------
# 6. 전체 크롤링 실행
# ----------------------------------------
def main():
    print(f"▶ {YEAR}년 {SEMESTER}학기 데이터 수집 시작")
    print(f"▶ 저장 경로: {OUTPUT_FILE}")
    
    departments = fetch_departments()
    print(f"총 {len(departments)}개 전공 발견\n")

    H_CODES = ["H1", "H2", "H3", "H4"]
    G_CODES = ["G31", "G32", "G333", "G344", "G355", "G9", "G19"]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        
        # 전공(H 계열)
        for d in departments:
            if d["code"] == "5185": continue # 교양 제외
                
            print(f"▶ 전공 {d['name']} 처리 중…")

            for h in H_CODES:
                courses = fetch_courses_by_major(d["code"], h)
                if courses:
                    print(f"  - {d['name']} ({h}): {len(courses)}개 과목 수집")
                
                grade_num = int(h[1])

                for c in courses:
                    syllabus_url = construct_syllabus_url(c["params"])
                    
                    doc = {
                        "id": f"{c['학수번호']}-{c['분반']}",
                        "content": (
                            f"과목명: {c['과목명']}\n"
                            f"학수번호: {c['학수번호']}\n"
                            f"분반: {c['분반']}\n"
                            f"전공: {d['name']}\n"
                            f"학년: {grade_num}학년\n"
                            f"담당교수: {c['담당교수']}\n"
                            f"학점: {c['학점']}\n"
                            f"강의시간: {c['강의시간']}\n"
                            f"강의계획서: {syllabus_url}"
                        ),
                        "metadata": {
                            "subject_name": c['과목명'],
                            "department": d['name'],
                            "grade": grade_num,
                            "professor": c['담당교수'],
                            "credit": c['학점'],
                            "year": int(YEAR),
                            "semester": int(SEMESTER),
                            "syllabus_url": syllabus_url
                        }
                    }
                    output.write(json.dumps(doc, ensure_ascii=False) + "\n")
                
                time.sleep(0.1)

        # 교양(G 계열)
        print("\n▶ 교양 영역 전체 수집 시작")
        for g in G_CODES:
            print(f"- 교양 영역 {g} 처리 중…")
            courses = fetch_courses_by_major("5185", g)
            if courses:
                print(f"  - 교양 {g}: {len(courses)}개 과목 수집")

            for c in courses:
                syllabus_url = construct_syllabus_url(c["params"])
                
                doc = {
                    "id": f"{c['학수번호']}-{c['분반']}",
                    "content": (
                        f"과목명: {c['과목명']}\n"
                        f"학수번호: {c['학수번호']}\n"
                        f"분반: {c['분반']}\n"
                        f"구분: 교양 {g}\n"
                        f"담당교수: {c['담당교수']}\n"
                        f"학점: {c['학점']}\n"
                        f"강의시간: {c['강의시간']}\n"
                        f"강의계획서: {syllabus_url}"
                    ),
                    "metadata": {
                        "subject_name": c['과목명'],
                        "department": "교양",
                        "grade": 0,
                        "professor": c['담당교수'],
                        "credit": c['학점'],
                        "year": int(YEAR),
                        "semester": int(SEMESTER),
                        "syllabus_url": syllabus_url,
                        "category": g
                    }
                }
                output.write(json.dumps(doc, ensure_ascii=False) + "\n")
            
            time.sleep(0.1)

    print(f"\n🎉 전체 크롤링 완료! → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
