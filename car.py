
import requests
import time

# ======================================================
# 1. 사용자 설정 (여기에 아이디/비번을 입력하세요)
# ======================================================
USER_ID = "yiknu01"
USER_PW = "yiknu01"

# ======================================================
# 2. URL 설정
# ======================================================
LOGIN_URL = "https://new.ubikhan.com/member/login"
CAR_STATUS_URL = "https://new.ubikhan.com/my_ubikhan/car_status"

# 브라우저인 척 속이기 위한 헤더 (차단 방지)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://new.ubikhan.com/main",
    "Origin": "https://new.ubikhan.com"
}

def get_shuttle_locations():
    # 세션 시작 (이 객체가 '브라우저' 역할을 하며 쿠키를 자동 관리함)
    session = requests.Session()
    
    # ------------------------------------------------------
    # 3. 로그인 수행
    # ------------------------------------------------------
    # HTML form에서 찾은 name 속성값들입니다.
    login_data = {
        "request_url": "map",  # hidden input 값
        "remember": "1",       # hidden input 값
        "login": USER_ID,      # 아이디 input name
        "password": USER_PW    # 비밀번호 input name
    }
    
    print("로그인 시도 중...")
    try:
        # session.post를 쓰면 로그인 성공 시 쿠키가 session 안에 저장됨
        res_login = session.post(LOGIN_URL, data=login_data, headers=HEADERS)
        
        # 302 리다이렉트 후 최종 응답 코드가 200이면 성공으로 간주
        if res_login.status_code == 200: 
            print("로그인 성공! (세션 획득 완료)")
        else:
            print(f"로그인 실패 또는 예상치 못한 응답: {res_login.status_code}")
            return None

    except Exception as e:
        print(f"로그인 중 에러 발생: {e}")
        return None

    # ------------------------------------------------------
    # 4. 버스 위치 데이터 요청 (저장된 쿠키 사용)
    # ------------------------------------------------------
    # car_status 요청에 필요한 데이터 (이전 분석 기반)
    car_payload = {
        "groupid": "",       
        "licenseid": "",     
        "startstatus": "",   # "1"로 하면 시동 켜진 차만, 비우면 전체
        "servicetype": ""    # 필요시 추가
    }
    
    print("버스 위치 정보 요청 중...")
    try:
        # 로그인된 session 객체로 요청을 보냄 (자동으로 쿠키가 포함됨)
        res_bus = session.post(CAR_STATUS_URL, data=car_payload, headers=HEADERS)
        
        if res_bus.status_code == 200:
            return res_bus.json() # JSON 데이터 반환
        else:
            print(f"데이터 요청 실패: {res_bus.status_code}")
            return None
            
    except Exception as e:
        print(f"데이터 요청 중 에러: {e}")
        return None

# ======================================================
# 5. 실행 및 결과 출력
# ======================================================
if __name__ == "__main__":
    data = get_shuttle_locations()
    
    if data and data.get("result") == True:
        print(f"\n총 {data['count']}대의 차량 데이터 수신 성공!\n")
        print("-" * 40)
        
        for bus in data['list']:
            name = bus['licenseid']      # 차량 이름 (예: 강남대학교 1호)
            lat = bus['lat']             # 위도
            lon = bus['lon']             # 경도
            is_running = "운행중" if bus['startstatus'] == "1" else "대기중(시동꺼짐)"
            last_time = bus['repotime']  # 마지막 보고 시간
            
            # 여기서 내 서비스 DB에 넣거나 가공하면 됩니다.
            print(f"🚌 [{name}] {is_running}")
            print(f"   📍 좌표: {lat}, {lon}")
            print(f"   🕒 시간: {last_time}")
            print("-" * 40)
    else:
        print("데이터를 가져오지 못했습니다.")