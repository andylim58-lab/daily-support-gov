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

# ── 키워드 필터 ──────────────────────────────────────────────
KEYWORDS = [
    '마케팅', '디지털마케팅', '온라인마케팅', '광고', '홍보', '판로', '판로개척',
    '유통', '온라인판로', '쇼핑몰', '라이브커머스', '콘텐츠', '브랜딩',
    '미디어', '방송', 'TV', 'CTV', 'OTT', '영상', 'SNS', '인플루언서',
    'AI마케팅', '데이터마케팅', '퍼포먼스', '전자상거래'
]

def is_relevant(title):
    title_lower = title.lower()
    return any(k.lower() in title_lower for k in KEYWORDS)

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
            if not title or not is_relevant(title):
                continue
            href = title_el.get_attribute("href") or "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310"
            post_date = normalize_date(cols[-1].text.strip())
            post_date = post_date[0] if post_date else today_str
            if post_date < cutoff_date:
                continue
            new_data.append({"title": title, "source": "중기부", "post_date": post_date, "deadline": "상세확인", "url": href})
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
            if not title or not is_relevant(title):
                continue
            href = title_el.get_attribute("href") or "https://www.bizinfo.go.kr"
            post_date = normalize_date(cols[2].text.strip())
            post_date = post_date[0] if post_date else today_str
            deadline = cols[3].text.strip()[:10] if len(cols) > 3 else "상세확인"
            if post_date < cutoff_date:
                continue
            new_data.append({"title": title, "source": "기업마당", "post_date": post_date, "deadline": deadline, "url": href})
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
            if not title or not is_relevant(title):
                continue
            href = title_el.get_attribute("href") or "https://www.kocca.kr"
            post_date = normalize_date(cols[1].text.strip())
            post_date = post_date[0] if post_date else today_str
            deadline = cols[2].text.strip()[:10] if len(cols) > 2 else "상세확인"
            if post_date < cutoff_date:
                continue
            new_data.append({"title": title, "source": "콘진원", "post_date": post_date, "deadline": deadline, "url": href})
        except:
            continue
except Exception as e:
    print(f"콘진원 오류: {e}")

# ── 4. NIPA (정보통신산업진흥원) ─────────────────────────────
print("🔎 NIPA 수집 중...")
try:
    for page in range(1, 4):
        driver.get(f"https://www.nipa.kr/home/2-2?curPage={page}")
        time.sleep(3)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        stop_page = False
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 3:
                    continue
                title_el = row.find_element(By.CSS_SELECTOR, "td a")
                title = title_el.text.strip()
                if not title or not is_relevant(title):
                    continue
                href = title_el.get_attribute("href") or "https://www.nipa.kr/home/2-2"
                post_date = normalize_date(cols[-1].text.strip())
                post_date = post_date[0] if post_date else today_str
                if post_date < cutoff_date:
                    stop_page = True
                    continue
                deadline_text = cols[1].text.strip() if len(cols) > 1 else "상세확인"
                new_data.append({
                    "title": title,
                    "source": "NIPA",
                    "post_date": post_date,
                    "deadline": deadline_text,
                    "url": href
                })
            except:
                continue
        if stop_page:
            break
except Exception as e:
    print(f"NIPA 오류: {e}")

# ── 5. 판판대로 (중소기업유통센터) ──────────────────────────
print("🔎 판판대로 수집 중...")
try:
    for page in range(1, 4):
        url = f"https://fanfandaero.kr/portal/v2/preSprtBizPbanc.do?pageIndex={page}"
        driver.get(url)
        time.sleep(4)
        items = driver.find_elements(By.CSS_SELECTOR, "ul.board-list li, table tbody tr, .card-item, .list-item")
        stop_page = False
        for item in items:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, "a")
                title = title_el.text.strip()
                if not title:
                    title = item.find_element(By.CSS_SELECTOR, "strong, span.title, .tit").text.strip()
                if not title or not is_relevant(title):
                    continue
                href = title_el.get_attribute("href") or url
                full_text = item.text
                dates = normalize_date(full_text)
                post_date = dates[0] if dates else today_str
                if post_date < cutoff_date:
                    stop_page = True
                    continue
                deadline = dates[1] if len(dates) > 1 else "상세확인"
                new_data.append({
                    "title": title,
                    "source": "판판대로",
                    "post_date": post_date,
                    "deadline": deadline,
                    "url": href
                })
            except:
                continue
        if stop_page:
            break
except Exception as e:
    print(f"판판대로 오류: {e}")

# ── 6. 창업진흥원 (KISED) ────────────────────────────────────
print("🔎 창업진흥원 수집 중...")
try:
    for page in range(1, 4):
        driver.get(f"https://www.kised.or.kr/board.es?mid=a10303000000&bid=0005&nPage={page}")
        time.sleep(3)
        items = driver.find_elements(By.CSS_SELECTOR, ".board_list li")
        if not items:
            items = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        stop_page = False
        for item in items:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, "a")
                title = title_el.text.strip()
                if not title or not is_relevant(title):
                    continue
                href = title_el.get_attribute("href") or "https://www.kised.or.kr/board.es?mid=a10303000000&bid=0005"
                full_text = item.text
                dates = normalize_date(full_text)
                post_date = dates[0] if dates else today_str
                deadline = dates[1] if len(dates) > 1 else "상세확인"
                if post_date < cutoff_date:
                    stop_page = True
                    continue
                status = "종료" if "종료" in full_text else "진행중"
                new_data.append({
                    "title": title,
                    "source": "창업진흥원",
                    "post_date": post_date,
                    "deadline": f"{deadline} ({status})",
                    "url": href
                })
            except:
                continue
        if stop_page:
            break
except Exception as e:
    print(f"창업진흥원 오류: {e}")

driver.quit()
print(f"✅ 오늘 신규 수집: {len(new_data)}건")

# ── 누적 데이터 로드 및 병합 ─────────────────────────────────
HISTORY_FILE = "history.json"

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

existing_keys = {(item["title"], item["post_date"]) for item in history}
added = 0
for item in new_data:
    key = (item["title"], item["post_date"])
    if key not in existing_keys:
        history.append(item)
        existing_keys.add(key)
        added += 1

print(f"✅ 신규 추가: {added}건 / 누적 총 {len(history)}건")
history.sort(key=lambda x: x["post_date"], reverse=True)

with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# ── index.html 생성 ──────────────────────────────────────────
PER_PAGE = 20
all_rows_js = json.dumps(history, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>지원사업 통합 공고 (마케팅·판로·광고)</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; max-width: 1200px; margin: 0 auto; }}
    h1 {{ font-size: 1.4rem; }}
    .meta {{ color: #888; font-size: 0.85rem; margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; }}
    th {{ background: #f2f2f2; white-space: nowrap; }}
    tr:hover {{ background: #f9f9f9; }}
    a {{ color: #0070f3; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .pagination {{ margin-top: 20px; display: flex; flex-wrap: wrap; gap: 6px; }}
    .pagination button {{
      padding: 6px 12px; border: 1px solid #ddd; background: #fff;
      cursor: pointer; border-radius: 4px; font-size: 0.85rem;
    }}
    .pagination button.active {{
      background: #0070f3; color: #fff; border-color: #0070f3; font-weight: bold;
    }}
    .pagination button:hover:not(.active) {{ background: #f0f0f0; }}
  </style>
</head>
<body>
  <h1>📅 지원사업 통합 공고 (마케팅·판로·광고)</h1>
  <p class="meta">마지막 업데이트: {today_str} | 누적 총 <span id="total"></span>건</p>
  <table>
    <thead>
      <tr>
        <th>번호</th><th>제목</th><th>출처</th><th>공고일</th><th>마감일</th><th>링크</th>
      </tr>
    </thead>
    <tbody id="tableBody"></tbody>
  </table>
  <div class="pagination" id="pagination"></div>

  <script>
    const data = {all_rows_js};
    const PER_PAGE = {PER_PAGE};
    let currentPage = 1;

    document.getElementById("total").textContent = data.length;

    function renderTable(page) {{
      currentPage = page;
      const start = (page - 1) * PER_PAGE;
      const slice = data.slice(start, start + PER_PAGE);
      document.getElementById("tableBody").innerHTML = slice.map((item, i) => `
        <tr>
          <td>${{start + i + 1}}</td>
          <td>${{item.title}}</td>
          <td>${{item.source}}</td>
          <td>${{item.post_date}}</td>
          <td>${{item.deadline}}</td>
          <td><a href="${{item.url}}" target="_blank">링크</a></td>
        </tr>
      `).join("");
      renderPagination();
    }}

    function renderPagination() {{
      const totalPages = Math.ceil(data.length / PER_PAGE);
      const groupSize = 10;
      const groupStart = Math.floor((currentPage - 1) / groupSize) * groupSize + 1;
      const groupEnd = Math.min(groupStart + groupSize - 1, totalPages);
      let html = "";
      if (groupStart > 1) {{
        html += `<button onclick="renderTable(${{groupStart - 1}})">◀ 이전</button>`;
      }}
      for (let p = groupStart; p <= groupEnd; p++) {{
        html += `<button class="${{p === currentPage ? 'active' : ''}}" onclick="renderTable(${{p}})">${{p}}</button>`;
      }}
      if (groupEnd < totalPages) {{
        html += `<button onclick="renderTable(${{groupEnd + 1}})">다음 ▶</button>`;
      }}
      document.getElementById("pagination").innerHTML = html;
    }}

    renderTable(1);
  </script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ index.html 저장 완료")
