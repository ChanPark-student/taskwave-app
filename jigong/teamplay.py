#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
activity_scraper.py

– 전남대 공지사항(장학안내, 대학생활, 취업정보)
– Linkareer 대외활동
– 결과를 통합하여 CSV로 저장

필수 패키지:
    pip install requests beautifulsoup4 pandas
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# ---------- 설정 ----------
JNU_BASE_URL    = "https://www.jnu.ac.kr/WebApp/web/HOM/COM/Board/board.aspx"
JNU_CATEGORIES  = {"장학안내":1, "대학생활":2, "취업정보":3}
LINKAREER_URL   = "http://linkareer.com/list/activity"
PAGE_LIMIT      = 3      # Linkareer 몇 페이지까지 가져올지
OUTPUT_CSV_PATH = "activities.csv"

# ---------- JNU 공지 크롤러 ----------
def scrape_jnu(board_ids):
    entries = []
    for category, board_id in board_ids.items():
        params = {"boardID": board_id, "pageSize": 20, "pageIndex": 1}
        resp = requests.get(JNU_BASE_URL, params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table.board_list tbody tr")
        for tr in rows:
            cols = tr.find_all("td")
            if len(cols) < 3:
                continue
            link_tag = cols[1].find("a")
            title = link_tag.get_text(strip=True)
            href  = link_tag.get("href")
            link  = requests.compat.urljoin(JNU_BASE_URL, href)
            date  = cols[-1].get_text(strip=True)
            entries.append({
                "source": "JNU",
                "category": category,
                "title": title,
                "link": link,
                "date": date
            })
        time.sleep(0.5)  # 과도 요청 방지
    return entries

# ---------- Linkareer 대외활동 크롤러 ----------
def scrape_linkareer(pages):
    entries = []
    for page in range(1, pages + 1):
        params = {"page": page}
        resp = requests.get(LINKAREER_URL, params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".activity-list .item")  # 실제 클래스명 확인 필요
        for item in items:
            a_tag = item.select_one(".tit a") or item.find("a")
            title = a_tag.get_text(strip=True)
            href  = a_tag.get("href")
            link  = requests.compat.urljoin(LINKAREER_URL, href)
            date_tag = item.select_one(".date")
            date = date_tag.get_text(strip=True) if date_tag else ""
            entries.append({
                "source": "Linkareer",
                "category": "대외활동",
                "title": title,
                "link": link,
                "date": date
            })
        time.sleep(0.5)
    return entries

# ---------- 메인 ----------
def main():
    # JNU 스크래핑
    jnu_entries = scrape_jnu(JNU_CATEGORIES)
    # Linkareer 스크래핑
    lk_entries  = scrape_linkareer(PAGE_LIMIT)

    # 데이터프레임 및 CSV 저장
    df = pd.DataFrame(jnu_entries + lk_entries)
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} entries to {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()
