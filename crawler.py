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
    """텍스트에서 날짜 형태를 모두 찾아 YYYY-MM-DD로 변환"""
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    normalized = []
    for d in matches:
        nums = re.split(r'[-./]', d)
        if len(nums) == 3:
            y, m, d = nums
            if len(y) == 2: y = "20" + y
            normalized.append(f"{y}-{m.zfill(2)}-{d.zfill(2)}")
    # 중복 제거 및 시간순 정렬
    return sorted(list(set(normalized)))

# 1. 중소벤처기업부
print("🔎 중기부 수집 중...")
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    time.sleep(8) 
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        row_text = row.text.strip()
        if not row_text or "공지" in row_text or "결과가" in row_text:
            continue
            
        dates = extract_dates(row_text)
        start_date = dates[0] if dates else "2026-03-10"
        end_date = dates[1] if len(dates) > 1 else "상세확인"
        if start_date < target_date: continue
            
        try:
            a_tags = row.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                raw_text = a.get_attribute("textContent").strip()
                clean_text = re.sub(r'\s+', ' ', raw_text).strip()
                
                if len(clean_text) > 5:
                    clean_title = re.split(r'담당부서|공고번호|신청기간|첨부파일|등록일|조회', clean_text)[0].strip()
                    onclick = a.get_attribute("onclick") or ""
                    href = a.get_attribute("href") or ""
                    
                    num_match = re.search(r"bcIdx=(\d+)", href) or re.search(r"view\D*(\d+)", onclick) or re.search(r"(\d{5,})", onclick)
                    
                    if num_match:
                        best_link = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={num_match.group(1)}"
                    else:
                        best_link = "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310"
                        
                    crawled_data.append({'title': clean_title, 'source': '중기부', 'start': start_date, 'end': end_date, 'url': best_link})
                    break
        except: pass
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
        end_date = dates[1] if len(dates) > 1 else "상세확인"
        if start_date < target_date: continue
        
        a_tags = row.find_elements(By.TAG_NAME, "a")
        for a in a_tags:
            title = a.get_attribute("textContent").strip()
            if len(title) > 5:
                crawled_data.append({'title': title, 'source': '기업마당', 'start': start_date, 'end': end_date, 'url': "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"})
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
        end_date = dates[1] if len(dates) > 1 else "상세확인"
        if start_date < target_date: continue
        
        a_tags = row.find_elements(By.TAG_NAME, "a")
        for a in a_tags:
            title = a.get_attribute("textContent").strip()
            if len(title) > 5:
                crawled_data.append({'title': title, 'source': '콘진원', 'start': start_date, 'end': end_date, 'url': a.get_attribute('href')})
                break
except: pass

# 4. NIPA (정보통신산업진흥원
