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
        
        dates = extract_dates(
