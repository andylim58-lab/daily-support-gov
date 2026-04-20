import time
import re
import json
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ── 날짜 기준 ────────────────────────────────────────────────
today = datetime.today()
cutoff_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
today_str = today.strftime("%Y-%m-%d")

# ── Chrome 설정 ──────────────────────────────────────────────
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
chrome_options.binary_location = "/usr/bin/google-chrome"

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

new_data = []

# ── 날짜 정규화 ──────────────────────────────────────────────
def normalize_date(text):
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    results = []
    for d in matches:
        parts = re.split(r'[-./]', d)
        if len(parts) == 3:
            y, m, dd = parts
            if len(y) == 2:
