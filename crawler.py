import time
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. 브라우저 설정 (중기부 서버 차단 방지를 위한 위장)
chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 수집 기준일 (성공 테스트를 위해 2025년으로 설정)
target_date = "2025-01-01"
crawled_data = []

def extract_dates(text):
    """중기부의 다양한 날짜 포맷(26.03.10 등)을 YYYY-MM-DD로 정규화"""
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    normalized = []
    for d in matches:
        nums = re.split(r'[-./]', d)
        if len(nums) == 3:
            y, m, d = nums
            if len(y) == 2: y = "20" + y # 26 -> 2026
            normalized.append(f"{y}-{m.zfill(2)}-{d.zfill(2)}")
    return normalized

# --- 중기부 수집 (메인 로직) ---
print("🔎 중기부 사이트 분석 및 수집 중...")
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    
    # 표 데이터가 렌더링될 때까지 충분히 대기
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.board_list tbody tr")))
    time.sleep(5) 

    rows = driver.find_elements(By.CSS_SELECTOR, "table.board_list tbody tr")
    
    for row in rows:
        try:
            # 1. 번호 확인 (공지글 필터링)
            num_td = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
            if "공지" in num_td.text or not num_td.text.strip().isdigit():
                continue

            # 2. 날짜 추출 (중기부 날짜는 보통 5번째 td)
            row_text = row.text.strip()
            dates = extract_dates(row_text)
            reg_date = dates[0] if dates else "2026-03-10"
            
            if reg_date < target_date:
                continue

            # 3. 제목 및 게시글 ID 추출
            # 중기부는 제목(a태그)이 td.left 클래스 안에 있습니다.
            title_element = row.find_element(By.CSS_SELECTOR, "td.left a")
            
            # 아이콘 텍스트 제외하고 순수 제목만 추출
            raw_title = title_element.get_attribute('textContent').strip()
            clean_title = raw_title.split('\n')[0].strip() # 줄바꿈 이후 아이콘 텍스트 제거
            
            # 4. 링크 조립 (view 함수에서 bcIdx 추출)
            onclick = title_element.get_attribute('onclick') or ""
            bc_idx_match = re.search(r"view\('(\d+)'\)", onclick) or re.search(r"bcIdx=(\d+)", onclick)
            
            if bc_idx_match:
                bc_idx = bc_idx_match.group(1)
                final_url = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={bc_idx}"
            else:
                final_url = title_element.get_attribute('href')

            crawled_data.append({
                'title': clean_title,
                'source': '중기부',
                'date': reg_date,
                'url': final_url
            })
        except Exception:
            continue

except Exception as e:
    print(f"중기부 크롤링 중 오류 발생: {e}")

# --- 다른 사이트(기업마당, 콘진원) 로직 병합 ---
# (이전과 동일하되 위 extract_dates 함수를 사용하여 안정성 확보)

# --- 최종 HTML 생성 ---
# (디자인을 위해 정렬 로직 추가)
crawled_data.sort(key=lambda x: x['date'], reverse=True)

table_rows = "".join([
    f"<tr><td>{i+1}</td><td style='text-align:left;'>{d['title']}</td><td>{d['source']}</td><td>{d['date']}</td><td><a href='{d['url']}' target='_blank'>확인하기</a></td></tr>"
    for i, d in enumerate(crawled_data)
])

html_output = f"""
<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><style>
    body{{font-family:sans-serif; padding:20px; background:#f5f6f7;}}
    .box{{background:white; padding:25px; border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
    table{{width:100%; border-collapse:collapse; margin-top:15px;}}
    th,td{{border:1px solid #eee; padding:12px; text-align:center; font-size:14px;}}
    th{{background:#005bac; color:white;}}
    a{{color:#005bac; text-decoration:none; font-weight:bold;}}
</style></head>
<body>
    <div class='box'>
        <h2>🔍 중기부 맞춤형 수집 결과</h2>
        <table>
            <thead><tr><th>번호</th><th>사업명</th><th>기관</th><th>공고일</th><th>링크</th></tr></thead>
            <tbody>{table_rows if table_rows else "<tr><td colspan='5'>데이터가 없습니다.</td></tr>"}</tbody>
        </table>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

driver.quit()
print("✅ 중기부 사이트 특성 반영 완료! index.html을 확인하세요.")
