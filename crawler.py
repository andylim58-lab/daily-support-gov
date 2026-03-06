import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 브라우저 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

target_date = "2026-02-20"
crawled_data = []

def extract_dates(text):
    matches = re.findall(r'(?:20)?\d{2}[-./]\d{2}[-./]\d{2}', text)
    normalized = []
    for d in matches:
        d = d.replace('.', '-').replace('/', '-')
        if len(d) == 8: d = '20' + d
        normalized.append(d)
    return normalized

# --- 수집 로직 (간소화 버전) ---
sources = [
    ("중기부", "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310"),
    ("기업마당", "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"),
    ("콘진원", "https://www.kocca.kr/kocca/pims/list.do?menuNo=204104")
]

for name, url in sources:
    try:
        driver.get(url)
        time.sleep(5)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            dates = extract_dates(row.text)
            start_date = dates[0] if dates else "날짜확인불가"
            if start_date != "날짜확인불가" and start_date < target_date: continue
            a_tag = row.find_element(By.CSS_SELECTOR, "a")
            crawled_data.append({'title': a_tag.text.strip(), 'source': name, 'start': start_date, 'url': a_tag.get_attribute('href') if name != "기업마당" else url})
    except: pass

driver.quit()

# HTML 생성
table_rows = "".join([f"<tr><td>{i+1}</td><td>{d['title']}</td><td>{d['source']}</td><td>{d['start']}</td><td><a href='{d['url']}' target='_blank'>링크</a></td></tr>" for i, d in enumerate(crawled_data)])
html_content = f"<html><head><meta charset='utf-8'><style>table{{width:100%;border-collapse:collapse;}}th,td{{border:1px solid #ddd;padding:8px;text-align:center;}}th{{background:#f4f4f4;}}</style></head><body><h2>지원사업 공고</h2><table><thead><tr><th>번호</th><th>제목</th><th>출처</th><th>날짜</th><th>이동</th></tr></thead><tbody>{table_rows}</tbody></table></body></html>"

# ★ 파일명을 index.html로 강제 고정 ★
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
