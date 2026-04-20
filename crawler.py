import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ── 날짜 기준 (오늘부터 30일 이내) ──────────────────────────
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

crawled_data = []

# ── 날짜 정규화 ──────────────────────────────────────────────
def normalize_date(text):
    matches = re.findall(r'\d{2,4}[-./]\d{1,2}[-./]\d{1,2}', text)
    results = []
    for d in matches:
        parts = re.split(r'[-./]', d)
        if len(parts) == 3:
            y, m, dd = parts
            if len(y) == 2:
                y = "20" + y
            results.append(f"{y}-{m.zfill(2)}-{dd.zfill(2)}")
    return sorted(list(set(results)))

# ── 지역 필터 (서울/전국만) ──────────────────────────────────
def is_target_region(title):
    exclude_keywords = ['강원', '경기', '경남', '경북', '광주', '대구', '대전',
                        '부산', '세종', '울산', '인천', '전남', '전북', '제주',
                        '충남', '충북', '지방']
    if any(k in title for k in exclude_keywords):
        if '서울' not in title and '전국' not in title:
            return False
    return True

# ── 1. 중소벤처기업부 ────────────────────────────────────────
print("🔎 중기부 수집 중...")
try:
    driver.get("https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310")
    time.sleep(3)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 3:
                continue
            title_el = row.find_element(By.CSS_SELECTOR, "td a")
            title = title_el.text.strip()
            if not title:
                continue
            href = title_el.get_attribute("href") or "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310"
            post_date = cols[-1].text.strip()[:10]
            dates = normalize_date(post_date)
            post_date = dates[0] if dates else today_str
            if post_date < cutoff_date:
                continue
            if not is_target_region(title):
                continue
            crawled_data.append({
                "title": title,
                "source": "중기부",
                "post_date": post_date,
                "deadline": "상세확인",
                "url": href
            })
        except:
            continue
except Exception as e:
    print(f"중기부 오류: {e}")

# ── 2. 기업마당 ──────────────────────────────────────────────
print("🔎 기업마당 수집 중...")
try:
    driver.get("https://www.bizinfo.go.kr/sii/siia/selectSIIA200List.do")
    time.sleep(3)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 4:
                continue
            title_el = row.find_element(By.CSS_SELECTOR, "td a")
            title = title_el.text.strip()
            if not title:
                continue
            href = title_el.get_attribute("href") or "https://www.bizinfo.go.kr"
            post_date = normalize_date(cols[2].text.strip())
            post_date = post_date[0] if post_date else today_str
            deadline = cols[3].text.strip()[:10] if len(cols) > 3 else "상세확인"
            if post_date < cutoff_date:
                continue
            if not is_target_region(title):
                continue
            crawled_data.append({
                "title": title,
                "source": "기업마당",
                "post_date": post_date,
                "deadline": deadline,
                "url": href
            })
        except:
            continue
except Exception as e:
    print(f"기업마당 오류: {e}")

# ── 3. 콘텐츠진흥원 ─────────────────────────────────────────
print("🔎 콘진원 수집 중...")
try:
    driver.get("https://www.kocca.kr/kocca/pims/list.do?menuNo=204104")
    time.sleep(3)
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 3:
                continue
            title_el = row.find_element(By.CSS_SELECTOR, "td a")
            title = title_el.text.strip()
            if not title:
                continue
            href = title_el.get_attribute("href") or "https://www.kocca.kr"
            post_date = normalize_date(cols[1].text.strip())
            post_date = post_date[0] if post_date else today_str
            deadline = cols[2].text.strip()[:10] if len(cols) > 2 else "상세확인"
            if post_date < cutoff_date:
                continue
            crawled_data.append({
                "title": title,
                "source": "콘진원",
                "post_date": post_date,
                "deadline": deadline,
                "url": href
            })
        except:
            continue
except Exception as e:
    print(f"콘진원 오류: {e}")

driver.quit()

# ── 정렬 및 결과 출력 ────────────────────────────────────────
crawled_data.sort(key=lambda x: x["post_date"], reverse=True)
print(f"✅ 총 {len(crawled_data)}건 수집 완료")

# ── index.html 생성 ──────────────────────────────────────────
rows_html = ""
for i, item in enumerate(crawled_data, 1):
    rows_html += f"""
    <tr>
      <td>{i}</td>
      <td>{item['title']}</td>
      <td>{item['source']}</td>
      <td>{item['post_date']}</td>
      <td>{item['deadline']}</td>
      <td><a href="{item['url']}" target="_blank">링크</a></td>
    </tr>"""

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>지원사업 통합 공고</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    h1 {{ font-size: 1.4rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f2f2f2; }}
    tr:hover {{ background: #f9f9f9; }}
    a {{ color: #0070f3; }}
    .meta {{ color: #888; font-size: 0.8rem; margin-bottom: 10px; }}
  </style>
</head>
<body>
  <h1>📅 지원사업 통합 공고</h1>
  <p class="meta">마지막 업데이트: {today_str} | 총 {len(crawled_data)}건 (최근 30일 기준)</p>
  <table>
    <thead>
      <tr>
        <th>번호</th><th>제목</th><th>출처</th><th>공고일</th><th>마감일</th><th>링크</th>
      </tr>
    </thead>
    <tbody>{rows_html}
    </tbody>
  </table>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ index.html 저장 완료")
