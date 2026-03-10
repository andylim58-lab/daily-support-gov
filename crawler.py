import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. 브라우저 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 데이터가 많이 나오도록 기준일을 2025년으로 설정 (성공 확인 후 날짜 조정 가능)
target_date = "2025-01-01"
crawled_data = []

def extract_dates(text):
    """문자열에서 다양한 날짜 형식을 찾아 YYYY-MM-DD로 변환"""
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    normalized = []
    for d in matches:
        nums = re.split(r'[-./]', d)
        if len(nums) == 3:
            year, month, day = nums
            if len(year) == 2: year = "20" + year
            normalized.append(f"{year}-{month.zfill(2)}-{day.zfill(2)}")
    return normalized

# --- 수집 시작 ---

# 1. 중소벤처기업부 (특별 관리)
print("🔎 중기부 수집 중...")
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    time.sleep(8)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        txt = row.text.strip()
        if not txt or "공지" in txt or "결과가 없습니다" in txt: continue
        
        dates = extract_dates(txt)
        start_date = dates[0] if dates else "2026-03-10"
        if start_date < target_date: continue

        try:
            # 중기부는 td.left 내부의 a 태그를 찾아야 함
            a_tag = row.find_element(By.CSS_SELECTOR, "td.left a")
            title = a_tag.text.strip()
            
            # 자바스크립트 호출 인자에서 게시글 번호(bcIdx) 추출
            onclick_val = a_tag.get_attribute('onclick')
            if onclick_val and 'view' in onclick_val:
                bc_idx = re.findall(r'\d+', onclick_val)[0]
                link = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={bc_idx}"
            else:
                link = a_tag.get_attribute('href')
            
            if title:
                crawled_data.append({'title': title, 'source': '중기부', 'start': start_date, 'url': link})
        except: continue
except Exception as e: print(f"중기부 에러: {e}")

# 2. 기업마당
print("🔎 기업마당 수집 중...")
try:
    driver.get("https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do")
    time.sleep(6)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        txt = row.text.strip()
        dates = extract_dates(txt)
        start_date = dates[0] if dates else "2026-03-10"
        if start_date < target_date: continue
        try:
            a_tag = row.find_element(By.TAG_NAME, "a")
            crawled_data.append({'title': a_tag.text.strip(), 'source': '기업마당', 'start': start_date, 'url': "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"})
        except: continue
except Exception as e: print(f"기업마당 에러: {e}")

# 3. 한국콘텐츠진흥원
print("🔎 콘진원 수집 중...")
try:
    driver.get("https://www.kocca.kr/kocca/pims/list.do?menuNo=204104")
    time.sleep(6)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        txt = row.text.strip()
        dates = extract_dates(txt)
        start_date = dates[0] if dates else "2026-03-10"
        if start_date < target_date: continue
        try:
            a_tag = row.find_element(By.TAG_NAME, "a")
            crawled_data.append({'title': a_tag.text.strip(), 'source': '콘진원', 'start': start_date, 'url': a_tag.get_attribute('href')})
        except: continue
except Exception as e: print(f"콘진원 에러: {e}")

driver.quit()

# --- HTML 파일 생성 ---
if not crawled_data:
    table_rows = "<tr><td colspan='5'>데이터를 불러오는 중이거나 최신 공고가 없습니다.</td></tr>"
else:
    table_rows = "".join([f"<tr><td>{i+1}</td><td style='text-align:left;'>{d['title']}</td><td>{d['source']}</td><td>{d['start']}</td><td><a href='{d['url']}' target='_blank'>링크</a></td></tr>" for i, d in enumerate(crawled_data)])

html_content = f"""
<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><title>정부지원사업 통합공고</title><style>
    body{{font-family:'Malgun Gothic', sans-serif; padding:20px; line-height:1.6;}}
    h2{{color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:10px;}}
    table{{width:100%; border-collapse:collapse; margin-top:20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}}
    th,td{{border:1px solid #eee; padding:12px; text-align:center;}}
    th{{background:#3498db; color:white;}}
    tr:nth-child(even){{background:#f8f9fa;}}
    a{{color:#3498db; text-decoration:none; font-weight:bold;}}
    a:hover{{text-decoration:underline;}}
</style></head>
<body>
    <h2>📅 정부지원사업 통합 공고 (2026-03-10 업데이트)</h2>
    <p>중소벤처기업부, 기업마당, 콘진원의 최신 정보를 한곳에 모았습니다.</p>
    <table>
        <thead><tr><th>번호</th><th>제목</th><th>출처</th><th>공고일</th><th>이동</th></tr></thead>
        <tbody>{table_rows}</tbody>
    </table>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("✅ index.html 생성 완료!")
