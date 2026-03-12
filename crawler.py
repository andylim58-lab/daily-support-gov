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
    return sorted(list(set(normalized)))

# 타지역 전용 공고 필터링 (서울 및 전국 공고만 포함)
def is_target_region(title):
    exclude_keywords = ['강원', '경기', '경남', '경북', '광주', '대구', '대전', '부산', '세종', '울산', '인천', '전남', '전북', '제주', '충남', '충북', '지방']
    if any(k in title for k in exclude_keywords):
        if '서울' not in title and '전국' not in title:
            return False
    return True

# 1. 중소벤처기업부
print("🔎 중기부 수집 중...")
