import time
from datetime import datetime
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

print("🤖 지원사업 수집 및 index.html 생성을 시작합니다...")

# 브라우저 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080") 
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

target_date = "2026-02-20" # 기준일
crawled_data = []

def extract_dates(text):
    """YY.MM.DD 형식을 YYYY-MM-DD로 정규화합니다."""
    matches = re.findall(r'(?:20)?\d{2}[-./]\d{2}[-./]\d{2}', text)
    normalized_dates = []
    for d in matches:
        d = d.replace('.', '-').replace('/', '-')
        if len(d) == 8: # 26-02-20 -> 2026-02-20
            d = '20' + d
        normalized_dates.append(d)
    return normalized_dates

# --- 1. 중소벤처기업부 ---
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    time.sleep(5) 
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        dates = extract_dates(row.text)
        start_date = dates[0] if len(dates) > 0 else "날짜확인불가"
        if start_date != "날짜확인불가" and start_date < target_date: continue
        a_tag = row.find_element(By.CSS_SELECTOR, "a")
        crawled_data.append({'title': a_tag.text.strip(), 'source': '중기부', 'start': start_date, 'end': dates[1] if len(dates) > 1 else "상세확인", 'url': a_tag.get_attribute('href')})
except: pass

# --- 2. 기업마당 ---
try:
    driver.get("https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do")
    time.sleep(5)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        dates = extract_dates(row.text)
        start_date = dates[0] if len(dates) > 0 else "날짜확인불가"
        if start_date != "날짜확인불가" and start_date < target_date: continue
        a_tag = row.find_element(By.CSS_SELECTOR, "a")
        crawled_data.append({'title': a_tag.text.strip(), 'source': '기업마당', 'start': start_date, 'end': dates[1] if len(dates) > 1 else "상세확인", 'url': "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"})
except: pass

# --- 3. 한국콘텐츠진흥원 ---
try:
    driver.get("https://www.kocca.kr/kocca/pims/list.do?menuNo=204104")
    time.sleep(5)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        dates = extract_dates(row.text)
        start_date = dates[0] if len(dates) > 0 else "날짜확인불가"
        if start_date != "날짜확인불가" and start_date < target_date: continue
        a_tag = row.find_element(By.CSS_SELECTOR, "a")
        crawled_data.append({'title': a_tag.text.strip(), 'source': '콘진원', 'start': start_date, 'end': dates[1] if len(dates) > 1 else "상세확인", 'url': a_tag.get_attribute('href')})
except: pass

driver.quit()

# --- HTML 생성 ---
table_rows = ""
for idx, data in enumerate(crawled_data, 1):
    table_rows += f"<tr><td>{idx}</td><td style='text-align:left;'>{data['title']}</td><td>{data['source']}</td><td>{data['start']}</td><td>{data['end']}</td><td><a href='{data['url']}' target='_blank'>바로가기</a></td></tr>"

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>지원사업 목록</title><style>body{{font-family:sans-serif;padding:20px;}}table{{width:100%;border-collapse:collapse;}}th,td{{border:1px solid #ddd;padding:12px;text-align:center;}}th{{background:#f4f4f4;}}</style></head>
<body><h2>📅 지원사업 통합 공고 (기준: 2월 20일 이후)</h2><table><thead><tr><th>번호</th><th>제목</th><th>출처</th><th>시작일</th><th>마감일</th><th>링크</th></tr></thead><tbody>{table_rows}</tbody></table></body>
</html>
"""

# ★★★ 여기가 가장 중요합니다! ★★★
# 경로 계산 없이 현재 폴더에 index.html 이라는 이름으로 바로 저장합니다.
file_path = "index.html" 

with open(file_path, "w", encoding="utf-8") as file:
    file.write(html_content)

print(f"🎉 성공! {file_path} 파일이 생성되었습니다.")
