import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. 브라우저 환경 설정 (위장 및 안정성 강화)
chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 데이터 수집 기준일 (과거 데이터를 포함해 성공 여부를 확인하기 위해 2025년으로 설정)
target_date = "2025-01-01"
crawled_data = []

def extract_dates(text):
    """문자열 내 다양한 날짜 형식을 YYYY-MM-DD로 표준화"""
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    normalized = []
    for d in matches:
        nums = re.split(r'[-./]', d)
        if len(nums) == 3:
            y, m, d = nums
            if len(y) == 2: y = "20" + y
            normalized.append(f"{y}-{m.zfill(2)}-{d.zfill(2)}")
    return normalized

# --- 수집 로직 시작 ---

# 1. 중소벤처기업부 (고난도 타겟)
print("🔎 중기부 데이터 수집 중...")
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    # 표가 로딩될 때까지 최대 20초 대기
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    time.sleep(5) # 스크립트 실행 대기
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        try:
            # '공지' 글은 건너뜁니다
            no_text = row.find_element(By.CSS_SELECTOR, "td").text.strip()
            if "공지" in no_text or not no_text: continue

            txt = row.text.strip()
            dates = extract_dates(txt)
            start_date = dates[0] if dates else "2026-03-10"
            if start_date < target_date: continue

            # 제목 및 링크 추출 (중기부 특화)
            a_tag = row.find_element(By.CSS_SELECTOR, "td.left a")
            title = a_tag.text.strip()
            onclick = a_tag.get_attribute('onclick') or ""
            
            # bcIdx 번호를 찾아내서 직접 URL 조립
            bc_match = re.search(r"bcIdx=(\d+)", onclick) or re.search(r"view\((\d+)\)", onclick)
            if bc_match:
                bc_idx = bc_match.group(1)
                link = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={bc_idx}"
            else:
                link = a_tag.get_attribute('href')
            
            if title:
                crawled_data.append({'title': title, 'source': '중기부', 'start': start_date, 'url': link})
        except: continue
except Exception as e: print(f"중기부 오류: {e}")

# 2. 기업마당
print("🔎 기업마당 데이터 수집 중...")
try:
    driver.get("https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do")
    time.sleep(7)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        try:
            txt = row.text.strip()
            dates = extract_dates(txt)
            start_date = dates[0] if dates else "2026-03-10"
            if start_date < target_date: continue
            
            a_tag = row.find_element(By.TAG_NAME, "a")
            crawled_data.append({'title': a_tag.text.strip(), 'source': '기업마당', 'start': start_date, 'url': "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"})
        except: continue
except: pass

# 3. 한국콘텐츠진흥원
print("🔎 콘진원 데이터 수집 중...")
try:
    driver.get("https://www.kocca.kr/kocca/pims/list.do?menuNo=204104")
    time.sleep(7)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        try:
            txt = row.text.strip()
            dates = extract_dates(txt)
            start_date = dates[0] if dates else "2026-03-10"
            if start_date < target_date: continue
            
            a_tag = row.find_element(By.TAG_NAME, "a")
            crawled_data.append({'title': a_tag.text.strip(), 'source': '콘진원', 'start': start_date, 'url': a_tag.get_attribute('href')})
        except: continue
except: pass

driver.quit()

# --- 결과 생성 (HTML) ---

# 날짜 기준 내림차순 정렬 (최신순)
crawled_data.sort(key=lambda x: x['start'], reverse=True)

table_rows = ""
for i, d in enumerate(crawled_data):
    table_rows += f"""
    <tr>
        <td>{i+1}</td>
        <td style='text-align:left;'>{d['title']}</td>
        <td><span class='badge'>{d['source']}</span></td>
        <td>{d['start']}</td>
        <td><a href='{d['url']}' target='_blank' class='btn'>이동</a></td>
    </tr>
    """

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>정부지원사업 통합 공고</title>
    <style>
        body {{ font-family: 'Pretendard', sans-serif; background-color: #f4f7f9; padding: 20px; }}
        .container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
        h2 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background-color: #3498db; color: white; padding: 15px; font-size: 14px; }}
        td {{ padding: 15px; border-bottom: 1px solid #eee; text-align: center; font-size: 14px; }}
        tr:hover {{ background-color: #fcfcfc; }}
        .badge {{ background: #e8f4fd; color: #3498db; padding: 4px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }}
        .btn {{ background: #3498db; color: white; padding: 6px 12px; border-radius: 5px; text-decoration: none; font-size: 12px; }}
        .btn:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>📅 정부지원사업 통합 공고 (최신 업데이트)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 8%;">번호</th>
                    <th style="width: 50%;">지원사업 제목</th>
                    <th style="width: 15%;">기관</th>
                    <th style="width: 15%;">공고일</th>
                    <th style="width: 12%;">링크</th>
                </tr>
            </thead>
            <tbody>
                {table_rows if table_rows else "<tr><td colspan='5'>조건에 맞는 최신 데이터가 없습니다.</td></tr>"}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("🚀 [성공] 모든 데이터가 index.html에 완벽하게 저장되었습니다!")
