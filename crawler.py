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
            # 가장 긴 텍스트를 가진 a태그를 찾아 불필요한 꼬리표 절제
            a_tags = row.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                raw_text = a.get_attribute("textContent").strip()
                clean_text = re.sub(r'\s+', ' ', raw_text).strip()
                
                if len(clean_text) > 5:
                    # 쓰레기 텍스트 제거
                    clean_title = re.split(r'담당부서|공고번호|신청기간|첨부파일|등록일|조회', clean_text)[0].strip()
                    
                    onclick = a.get_attribute("onclick") or ""
                    href = a.get_attribute("href") or ""
                    
                    # 숨겨진 게시글 고유번호(bcIdx) 적출 시도
                    num_match = re.search(r"bcIdx=(\d+)", href) or re.search(r"view\D*(\d+)", onclick) or re.search(r"(\d{5,})", onclick)
                    
                    if num_match:
                        best_link = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={num_match.group(1)}"
                    else:
                        best_link = "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310" # 실패 시 목록으로
                        
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

driver.quit()

# 최신 공고일 기준 정렬
crawled_data.sort(key=lambda x: x['start'], reverse=True)

table_rows = "".join([f"<tr><td>{i+1}</td><td style='text-align:left;'>{d['title']}</td><td>{d['source']}</td><td>{d['start']}</td><td>{d['end']}</td><td><a href='{d['url']}' target='_blank'>링크</a></td></tr>" for i, d in enumerate(crawled_data)])

# 페이징 처리가 포함된 HTML 생성
html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset='utf-8'>
    <title>정부지원사업 통합공고</title>
    <style>
        body{{font-family:sans-serif; padding:20px; background:#f4f7f9;}}
        .box{{background:white; padding:20px; border-radius:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}}
        table{{width:100%; border-collapse:collapse; margin-top:20px; font-size: 14px;}}
        th,td{{border:1px solid #ddd; padding:12px; text-align:center;}}
        th{{background:#2c3e50; color:white;}}
        tr:hover {{ background-color: #f9f9f9; }}
        a{{color:#3498db; text-decoration:none; font-weight:bold;}}
        .pagination {{ text-align: center; margin-top: 20px; }}
        .pagination button {{ margin: 0 5px; padding: 8px 12px; border: 1px solid #ddd; background-color: white; cursor: pointer; border-radius: 4px; }}
        .pagination button.active {{ background-color: #3498db; color: white; border: 1px solid #3498db; }}
        .pagination button:hover:not(.active) {{ background-color: #f0f0f0; }}
    </style>
</head>
<body>
    <div class='box'>
        <h2>📅 지원사업 통합 공고</h2>
        <table id="myTable">
            <thead>
                <tr>
                    <th style="width: 5%;">번호</th>
                    <th style="width: 45%;">제목</th>
                    <th style="width: 10%;">출처</th>
                    <th style="width: 15%;">공고일</th>
                    <th style="width: 15%;">마감일</th>
                    <th style="width: 10%;">링크</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                {table_rows if table_rows else "<tr><td colspan='6'>조건에 맞는 데이터가 없습니다.</td></tr>"}
            </tbody>
        </table>
        <div id="pagination" class="pagination"></div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const rowsPerPage = 15;
            const rows = document.querySelectorAll('#tableBody tr');
            const rowsCount = rows.length;
            const pageCount = Math.ceil(rowsCount / rowsPerPage);
            const paginationWrapper = document.getElementById('pagination');

            // 항목이 없을 경우 페이징 스킵
            if(rows[0].innerText.includes('조건에 맞는 데이터가 없습니다')) return;

            function displayPage(page) {{
                let start = (page - 1) * rowsPerPage;
                let end = start + rowsPerPage;
                
                rows.forEach((row, index) => {{
                    row.style.display = (index >= start && index < end) ? '' : 'none';
                }});
                setupPagination(page);
            }}

            function setupPagination(currentPage) {{
                paginationWrapper.innerHTML = '';
                for (let i = 1; i <= pageCount; i++) {{
                    let btn = document.createElement('button');
                    btn.innerText = i;
                    if (i === currentPage) btn.classList.add('active');
                    
                    btn.addEventListener('click', function() {{
                        displayPage(i);
                        window.scrollTo(0, 0); // 페이지 변경 시 맨 위로 이동
                    }});
                    paginationWrapper.appendChild(btn);
                }}
            }}

            if (rowsCount > 0) displayPage(1);
        }});
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
