import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

target_date = "2025-01-01"
crawled_data = []

def extract_dates(text):
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    normalized = []
    for d in matches:
        nums = re.split(r'[-./]', d)
        if len(nums) == 3:
            y, m, d = nums
            if len(y) == 2: y = "20" + y
            normalized.append(f"{y}-{m.zfill(2)}-{d.zfill(2)}")
    return normalized

# 1. 중소벤처기업부 (가장 방어적인 무차별 추출 로직)
print("🔎 중기부 수집 중...")
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    time.sleep(8) # 강제 로딩 대기
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        row_text = row.text.strip()
        if not row_text or "공지" in row_text or "결과가" in row_text:
            continue
            
        dates = extract_dates(row_text)
        start_date = dates[0] if dates else "2026-03-10"
        if start_date < target_date: continue
            
        a_tags = row.find_elements(By.TAG_NAME, "a")
        best_title = ""
        best_link = ""
        
        # 행 안의 모든 a태그를 뒤져서 가장 긴 텍스트를 제목으로 채택
        for a in a_tags:
            text = a.get_attribute("textContent").strip()
            clean_text = re.sub(r'\s+', ' ', text).strip()
            
            if len(clean_text) > len(best_title):
                best_title = clean_text
                onclick = a.get_attribute("onclick") or ""
                href = a.get_attribute("href") or ""
                
                # 숫자 5자리 이상이면 무조건 게시글 번호로 간주
                num_match = re.search(r"(\d{5,})", onclick) or re.search(r"bcIdx=(\d+)", href)
                
                if num_match:
                    best_link = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={num_match.group(1)}"
                else:
                    best_link = href

        # 글자 수가 3자 이상일 때만 데이터로 인정
        if len(best_title) > 3:
            crawled_data.append({'title': best_title, 'source': '중기부', 'start': start_date, 'url': best_link})
except Exception as e:
    print(f"중기부 오류: {e}")

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
        
        a_tags = row.find_elements(By.TAG_NAME, "a")
        for a in a_tags:
            title = a.get_attribute("textContent").strip()
            if len(title) > 5:
                crawled_data.append({'title': title, 'source': '기업마당', 'start': start_date, 'url': "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"})
                break
except: pass

# 3. 콘진원
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
        
        a_tags = row.find_elements(By.TAG_NAME, "a")
        for a in a_tags:
            title = a.get_attribute("textContent").strip()
            if len(title) > 5:
                crawled_data.append({'title': title, 'source': '콘진원', 'start': start_date, 'url': a.get_attribute('href')})
                break
except: pass

driver.quit()

# 최신순 정렬
crawled_data.sort(key=lambda x: x['start'], reverse=True)

table_rows = "".join([f"<tr><td>{i+1}</td><td style='text-align:left;'>{d['title']}</td><td>{d['source']}</td><td>{d['start']}</td><td><a href='{d['url']}' target='_blank'>확인하기</a></td></tr>" for i, d in enumerate(crawled_data)])

html_content = f"""
<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><title>정부지원사업 통합공고</title><style>
    body{{font-family:sans-serif; padding:20px; background:#f4f7f9;}}
    .box{{background:white; padding:20px; border-radius:10px;}}
    table{{width:100%; border-collapse:collapse; margin-top:20px;}}
    th,td{{border:1px solid #ddd; padding:12px; text-align:center;}}
    th{{background:#2c3e50; color:white;}}
    a{{color:#3498db; text-decoration:none; font-weight:bold;}}
</style></head>
<body>
    <div class='box'>
        <h2>📅 지원사업 통합 공고 (최종)</h2>
        <table>
            <thead><tr><th>번호</th><th>제목</th><th>출처</th><th>공고일</th><th>링크</th></tr></thead>
            <tbody>{table_rows if table_rows else "<tr><td colspan='5'>조건에 맞는 데이터가 없습니다.</td></tr>"}</tbody>
        </table>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
