import time
from datetime import datetime
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

print("🤖 날짜 판독기를 업그레이드하여 공고 수집을 시작합니다...")

chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080") 
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

today_str = datetime.today().strftime('%Y-%m-%d')
target_date = "2026-02-20" # 기준일
crawled_data = []

def extract_dates(text):
    """YYYY.MM.DD 뿐만 아니라 YY.MM.DD (예: 26.02.20) 형식도 찾아내어 통일합니다"""
    # 20이 있거나 없거나 숫자 2개-숫자 2개-숫자 2개 패턴을 모두 찾습니다.
    matches = re.findall(r'(?:20)?\d{2}[-./]\d{2}[-./]\d{2}', text)
    normalized_dates = []
    for d in matches:
        d = d.replace('.', '-').replace('/', '-')
        if len(d) == 8: # 26-02-20 처럼 짧은 형태면 앞에 20을 붙여 2026-02-20으로 만듦
            d = '20' + d
        normalized_dates.append(d)
    return normalized_dates

# --- 1. 중소벤처기업부 ---
print("▶ 중소벤처기업부 탐색 중...")
try:
    mss_url = "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310"
    driver.get(mss_url)
    time.sleep(5) 
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    count = 0
    for row in rows:
        text_content = row.text
        dates = extract_dates(text_content)
        
        start_date = dates[0] if len(dates) > 0 else "날짜확인불가"
        end_date = dates[1] if len(dates) > 1 else "상세확인"
        
        if start_date != "날짜확인불가" and start_date < target_date:
            continue
            
        a_tag = row.find_element(By.CSS_SELECTOR, "a")
        title = a_tag.text.strip()
        
        if title and len(title) > 10:
            link = a_tag.get_attribute('href')
            onclick = a_tag.get_attribute('onclick')
            if link and ("javascript" in link.lower() or link.endswith("#")) and onclick:
                numbers = re.findall(r'\d+', onclick)
                if numbers:
                    post_id = max(numbers, key=len)
                    link = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={post_id}"
                else:
                    link = mss_url 
                    
            crawled_data.append({'title': title, 'source': '중기부', 'start': start_date, 'end': end_date, 'url': link})
            count += 1
            
    print(f"✅ 중기부 {count}개 수집 완료 (2/20 이후)")
except Exception as e:
    print(f"❌ 중기부 에러: {e}")

# --- 2. 기업마당 ---
print("▶ 기업마당 탐색 중...")
try:
    biz_url = "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"
    driver.get(biz_url)
    time.sleep(5) 
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    count = 0
    for row in rows:
        text_content = row.text
        dates = extract_dates(text_content)
        start_date = dates[0] if len(dates) > 0 else "날짜확인불가"
        end_date = dates[1] if len(dates) > 1 else "상세확인"
        
        if start_date != "날짜확인불가" and start_date < target_date:
            continue
            
        try:
            a_tag = row.find_element(By.CSS_SELECTOR, "a")
            title = a_tag.text.strip()
            link = a_tag.get_attribute('href')
            
            if title and len(title) > 10:
                if link and ("javascript" in link.lower() or link.endswith("#")):
                    link = biz_url
                crawled_data.append({'title': title, 'source': '기업마당', 'start': start_date, 'end': end_date, 'url': link})
                count += 1
        except:
            continue
            
    print(f"✅ 기업마당 {count}개 수집 완료 (2/20 이후)")
except Exception as e:
    print(f"❌ 기업마당 에러: {e}")

# --- 3. 한국콘텐츠진흥원 (접수시작일/마감일 반영) ---
print("▶ 한국콘텐츠진흥원 탐색 중...")
try:
    kocca_url = "https://www.kocca.kr/kocca/pims/list.do?menuNo=204104"
    driver.get(kocca_url)
    time.sleep(3)
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    count = 0
    for row in rows:
        text_content = row.text
        # 업그레이드된 함수가 26.02.20을 2026-02-20으로 자동 변환해줍니다!
        dates = extract_dates(text_content)
        start_date = dates[0] if len(dates) > 0 else "날짜확인불가"
        end_date = dates[1] if len(dates) > 1 else "상세확인"
        
        if start_date != "날짜확인불가" and start_date < target_date:
            continue
            
        a_tag = row.find_element(By.CSS_SELECTOR, "a")
        title = a_tag.text.strip()
        link = a_tag.get_attribute('href')
        if title:
            crawled_data.append({'title': title, 'source': '콘진원', 'start': start_date, 'end': end_date, 'url': link})
            count += 1
    print(f"✅ 콘진원 {count}개 수집 완료 (2/20 이후)")
except Exception as e:
    print(f"❌ 콘진원 에러: {e}")

driver.quit()

# --- HTML 조립 및 바탕화면 저장 ---
print("\n웹페이지(HTML)를 생성합니다...")
table_rows = ""
for idx, data in enumerate(crawled_data, 1):
    table_rows += f"""
    <tr>
        <td>{idx}</td>
        <td class="title-column" style="text-align: left; font-weight: 500;">{data['title']}</td>
        <td><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; background-color: #f1f3f5;">{data['source']}</span></td>
        <td>{data['start']}</td>
        <td>{data['end']}</td>
        <td><a href="{data['url']}" target="_blank" style="color: #000; text-decoration: none; border: 1px solid #000; padding: 4px 10px; font-size: 0.9em;">바로가기</a></td>
    </tr>
    """

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>지원사업 통합 공고 목록</title>
    <style>
        body {{ font-family: 'Pretendard', 'Malgun Gothic', sans-serif; background-color: #ffffff; color: #000000; margin: 40px; line-height: 1.6; }}
        h2 {{ text-align: center; margin-bottom: 30px; font-weight: 800; }}
        table {{ width: 100%; border-collapse: collapse; border-top: 2px solid #000; }}
        th {{ background-color: #f8f9fa; font-weight: bold; padding: 15px 10px; border-bottom: 1px solid #000; }}
        td {{ padding: 15px 10px; text-align: center; border-bottom: 1px solid #e3f2fd; }}
    </style>
</head>
<body>
    <h2>📅 오늘의 지원사업 통합 공고 (기준: 2월 20일 이후)</h2>
    <table>
        <thead>
            <tr><th>연번</th><th>공고제목</th><th>출처</th><th>시작일</th><th>마감일</th><th>URL</th></tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>
"""

current_folder = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_folder, "support_programs.html")

with open(file_path, "w", encoding="utf-8") as file:
    file.write(html_content)

print(f"🎉 완료되었습니다! 바탕화면의 'support_programs.html'을 열어보세요.")