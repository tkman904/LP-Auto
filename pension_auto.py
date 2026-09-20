import time
import re
import gspread
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

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
    PENSION_URL = "https://docs.google.com/spreadsheets/d/1SyDctyfajt1uVvQY9wQ_WaT2Ia3TwKOXWLZH2zFImjc/edit?gid=532635366#gid=532635366"
    PENSION_TAB_NAME = "연금720+ 회차별 당첨번호" 
    # ----------------------------------------

    print("=========================================")
    print(" 🚀 [Pension] 클라우드 자동화 스크립트 실행 🚀 ")
    print("=========================================\n")

    options = Options()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless') # 백그라운드 실행 (필수)
    options.add_argument('--no-sandbox') # 리눅스 서버 필수 옵션 1
    options.add_argument('--disable-dev-shm-usage') # 리눅스 서버 필수 옵션 2
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("👉 크롬 브라우저 엔진을 가동합니다...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    print("\n👉 연금복권 당첨번호 수집 및 시트 기록 중...")
    driver.get("https://www.dhlottery.co.kr/pt720/result")
    time.sleep(4) 
    
    try:
        if "간소화" in driver.page_source or "많이 찾는 서비스" in driver.page_source:
            try:
                print("   ⚠️ 간소화 페이지 감지! '추첨결과' 버튼을 클릭합니다...")
                link = driver.find_element(By.PARTIAL_LINK_TEXT, "연금복권720+ 추첨결과")
                link.click()
                time.sleep(4) 
            except:
                pass
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        text_data = soup.get_text(separator=' ', strip=True)
        
        round_match = re.search(r'([0-9]+)회', text_data)
        pen_round = round_match.group(1) if round_match else "알수없음"
        
        jo_match = re.search(r'([0-9]+)조', text_data)
        pen_jo = jo_match.group(1) if jo_match else "알수없음"
        
        ball_tags = soup.find_all(class_=re.compile(r'ball_720|ball'))
        pen_nums = [b.get_text(strip=True) for b in ball_tags if b.get_text(strip=True).isdigit()]
        
        if pen_round != "알수없음" and pen_jo != "알수없음" and len(pen_nums) >= 6:
            win_str = "".join(pen_nums[:6])
            
            # 회차와 조는 숫자(int)로, 당첨번호는 꼼수 없이 순수 문자열(str)로 전달
            pen_sheet_data = [int(pen_round), int(pen_jo), win_str]
            update_google_sheet(PENSION_URL, PENSION_TAB_NAME, pen_sheet_data)
        else:
            print("   🔴 연금복권 수집 실패: 화면에 번호가 없습니다.")
            
    except Exception as e:
        print(f"   ❌ 연금복권 수집/기록 에러: {e}")
        
    driver.quit()
    print("\n🎉 연금복권 작업 종료!")
