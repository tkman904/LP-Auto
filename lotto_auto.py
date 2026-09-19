import time
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def get_latest_lotto_round():
    """
    1회차 추첨 시간(2002년 12월 7일 밤 9시 30분)을 기준으로 
    현재 시점의 추첨 완료된 정확한 회차를 수학적으로 계산합니다.
    """
    first_draw = datetime.datetime(2002, 12, 7, 21, 30)
    now = datetime.datetime.now()
    diff = now - first_draw
    round_num = diff.days // 7 + 1
    return round_num

def update_google_sheet(sheet_url, sheet_name, data):
    """지정된 URL의 구글 시트에 데이터 한 줄 추가"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets', 
        'https://www.googleapis.com/auth/drive'
    ]
    try:
        credentials = Credentials.from_service_account_file('secret.json', scopes=scopes)
        gc = gspread.authorize(credentials)
        doc = gc.open_by_url(sheet_url)
        worksheet = doc.worksheet(sheet_name)
        
        # USER_ENTERED 옵션을 사용해 시트의 서식을 그대로 따르게 합니다.
        worksheet.append_row(data, value_input_option="USER_ENTERED")
        print(f"   ✅ 구글 시트 '{sheet_name}' 탭에 업데이트 완료: {data}")
    except Exception as e:
        print(f"   ❌ 구글 시트 업데이트 실패: {e}")

if __name__ == "__main__":
    # ----------------------------------------
    # 📝 구글 시트 URL 및 탭 이름을 세팅해주세요!
    # ----------------------------------------
    LOTTO_URL = "https://docs.google.com/spreadsheets/d/1v1OVIhSB9YzX8lQUgUWX2Il3Hh_K07ML6-Mjg7ic3is/edit?gid=1444913101#gid=1444913101"
    LOTTO_TAB_NAME = "로또 회차별 당첨번호"  
    # ----------------------------------------

    print("=========================================")
    print(" 🚀 [Lotto] 클라우드 자동화 스크립트 실행 🚀 ")
    print("=========================================\n")

    options = Options()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless') # 백그라운드 실행 (필수)
    options.add_argument('--no-sandbox') # 리눅스 서버 필수 옵션 1
    options.add_argument('--disable-dev-shm-usage') # 리눅스 서버 필수 옵션 2
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("👉 크롬 브라우저 엔진을 가동합니다...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    lotto_round = get_latest_lotto_round()
    lotto_url = f"https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do?srchLtEpsd={lotto_round}"
    
    print(f"\n👉 로또 {lotto_round}회차 당첨번호 수집 및 시트 기록 중...")
    driver.get(lotto_url)
    time.sleep(2) 
    
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        json_response = json.loads(body_text)
        json_data = json_response.get("data", {})
        json_list = json_data.get("list", [])
        
        if json_list:
            result = json_list[0]
            win_nums = [int(result[f"tm{i}WnNo"]) for i in range(1, 7)]
            bonus_num = int(result["bnsWnNo"])
            
            # [회차, 번호1~6, 보너스] 모두 숫자로 전달 (시트의 서식 자동 적용)
            lotto_sheet_data = [int(lotto_round)] + win_nums + [bonus_num]
            update_google_sheet(LOTTO_URL, LOTTO_TAB_NAME, lotto_sheet_data)
        else:
            print(f"   🔴 {lotto_round}회 추첨 결과가 아직 발표되지 않았습니다.")
            
    except Exception as e:
        print(f"   ❌ 로또 수집/기록 에러: {e}")
        
    driver.quit()
    print("\n🎉 로또 작업 종료!")