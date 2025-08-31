from __future__ import annotations
from typing import List, Dict, Optional, Tuple
import os, re, time, math, html as py_html
from urllib.parse import urlparse
from threading import Lock

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except Exception:
    HAS_WDM = False

# ───────── Driver singleton ─────────
_driver = None
_cfg = None
_lock = Lock()

def _make_options(*, headless: bool, user_data_dir: Optional[str], profile_dir: Optional[str]) -> Options:
    opts = Options()
    chrome_bin = os.environ.get("CHROME_BINARY") or os.environ.get("GOOGLE_CHROME_BIN")
    if chrome_bin:
        opts.binary_location = chrome_bin
    if headless:
        if os.environ.get("HEADLESS_MODE", "new").lower() == "legacy":
            opts.add_argument("--headless")
        else:
            opts.add_argument("--headless=new")
    opts.add_argument("--log-level=3")
    opts.add_argument("--disable-logging")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    if user_data_dir: opts.add_argument(f"--user-data-dir={user_data_dir}")
    if profile_dir:   opts.add_argument(f"--profile-directory={profile_dir}")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return opts

def _build_driver(headless: bool, user_data_dir: Optional[str], profile_dir: Optional[str]):
    opts = _make_options(headless=headless, user_data_dir=user_data_dir, profile_dir=profile_dir)
    last = None
    try:
        return webdriver.Chrome(options=opts)
    except Exception as e:
        last = e
    if HAS_WDM:
        try:
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=opts)
        except Exception as e:
            last = e
    for path in [
        r"C:\Chromedriver\chromedriver.exe",
        r"C:\Program Files\chromedriver\chromedriver.exe",
        r"C:\Program Files (x86)\chromedriver\chromedriver.exe",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ]:
        if os.path.isfile(path):
            try:
                service = Service(path)
                return webdriver.Chrome(service=service, options=opts)
            except Exception as e:
                last = e
    raise last or RuntimeError("Chrome WebDriver 초기화 실패")

def _get_driver(*, headless: bool) -> webdriver.Chrome:
    global _driver, _cfg
    with _lock:
        desired = {
            "headless": headless,
            "user_data_dir": os.environ.get("CHROME_USER_DATA_DIR"),
            "profile_dir": os.environ.get("CHROME_PROFILE_DIR"),
        }
        if _driver is not None and _cfg == desired:
            return _driver
        if _driver is not None:
            try: _driver.quit()
            except Exception: pass
        _driver = _build_driver(
            headless=desired["headless"],
            user_data_dir=desired["user_data_dir"],
            profile_dir=desired["profile_dir"],
        )
        _cfg = desired
        return _driver

# ───────── Utils ─────────
WEEKDAYS_KO = ["월","화","수","목","금","토","일"]
WEEKDAY_KO_FULL = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"]
WEEKDAY_EN = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
WEEKDAY_EN_FULL = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

TIME_RANGE_RE = re.compile(r'(?P<s_h>\d{1,2})[:\.]?(?P<s_m>\d{2})\s*[-~–]\s*(?P<e_h>\d{1,2})[:\.]?(?P<e_m>\d{2})')
SINGLE_TIME_RE = re.compile(r'\b(\d{1,2})[:\.]?([0-5]\d)\b')
ROOM_RE = re.compile(
    r"(?:[가-힣A-Za-z]{1,4}\s?\d{1,3}[A-Za-z]?\s*[-–]?\s?\d{2,4}\b)"
    r"|(?:\d{2,3}\s*[-–]\s*\d{2,4}\b)"
    r"|(?:[A-Za-z]{1,3}\d{2,4}\b)", flags=re.IGNORECASE)
NAME_RE = re.compile(r'^[가-힣]{2,4}$')

def _document_ready(driver: webdriver.Chrome, timeout: float = 20.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if driver.execute_script("return document.readyState") == "complete":
                return
        except Exception:
            pass
        time.sleep(0.2)

def _to_hhmm(h: int, m: int) -> str:
    h = max(0, min(23, int(h))); m = max(0, min(59, int(m)))
    return f"{h:02d}:{m:02d}"

def _weekday_from_text(s: str) -> Optional[str]:
    if not s: return None
    s = s.strip()
    for i, d in enumerate(WEEKDAY_KO_FULL):
        if d in s: return WEEKDAYS_KO[i]
    for i, d in enumerate(WEEKDAYS_KO):
        if d in s: return d
    for i, d in enumerate(WEEKDAY_EN_FULL):
        if d.lower() in s.lower(): return WEEKDAYS_KO[i]
    for i, d in enumerate(WEEKDAY_EN):
        if d.lower() in s.lower(): return WEEKDAYS_KO[i]
    return None

def _clean_subject_from_text(txt: str) -> Optional[str]:
    if not txt: return None
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    if not lines: return None
    cleaned_candidates = []
    for ln in lines:
        ln1 = TIME_RANGE_RE.sub("", ln)
        ln1 = SINGLE_TIME_RE.sub("", ln1)
        ln1 = ROOM_RE.sub("", ln1)
        ln1 = re.sub(r'[\(\[][^\)\]]*[\)\]]', '', ln1)
        ln1 = ln1.replace("~","").replace("-","")
        ln1 = re.sub(r"\s+","", ln1)
        if NAME_RE.fullmatch(ln1):  # 교수명 단독 제거
            continue
        if len(re.findall(r'[가-힣]', ln1)) >= 2:
            cleaned_candidates.append(ln1)
    if not cleaned_candidates:
        return None
    cleaned_candidates.sort(key=lambda z: (len(re.sub(r'[^가-힣]', '', z)), len(z)), reverse=True)
    return cleaned_candidates[0]

def _extract_subject(el) -> Optional[str]:
    # 에브리타임 계열: <h3>안에 과목이 정확히 박힘 → 최우선
    try:
        h3 = el.find_element(By.TAG_NAME, "h3")
        s = (h3.text or "").strip()
        if s:
            return _clean_subject_from_text(s) or s
    except Exception:
        pass
    for attr in ["data-title", "data-subject", "title", "aria-label"]:
        try:
            v = el.get_attribute(attr) or ""
        except Exception:
            v = ""
        subj = _clean_subject_from_text(v)
        if subj: return subj
    try:
        txt = el.text or ""
    except Exception:
        txt = ""
    return _clean_subject_from_text(txt)

def _rect(driver, el):
    return driver.execute_script(
        "const r=arguments[0].getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};", el
    )

# ───────── KOR 레이아웃 전용 파서 (너가 준 HTML 전용) ─────────
def _is_kor_table_layout(driver) -> bool:
    # 헤더에 시간 문자열(오전/오후)과 .subject 들이 동시에 존재하는지
    try:
        times = driver.find_elements(By.CSS_SELECTOR, "th .times .time")
        if not times: return False
        txt = " ".join([(t.text or "") for t in times])[:200]
        if not (("오전" in txt) or ("오후" in txt)):
            return False
        subs = driver.find_elements(By.CSS_SELECTOR, "td .cols .subject")
        return len(subs) > 0
    except Exception:
        return False

def _parse_kor_table_layout(driver: webdriver.Chrome, *, url: str) -> List[Dict]:
    driver.get(url)
    _document_ready(driver, 12)

    if not _is_kor_table_layout(driver):
        return []

    # 1) 기준 tr 찾기 (times가 들어있는 행)
    th_times = driver.find_element(By.CSS_SELECTOR, "th .times")
    tr = th_times.find_element(By.XPATH, "./ancestor::tr[1]")

    # 2) 요일 컬럼(td) 수집 (가시 컬럼만)
    tds = tr.find_elements(By.TAG_NAME, "td")
    visible_cols = []
    for td in tds:
        style = (td.get_attribute("style") or "").replace(" ", "").lower()
        if "display:none" in style:
            continue
        visible_cols.append(td)
    # 첫 번째 td가 월요일 컬럼이라고 가정 (주말 숨김이면 5칸)
    weekday_map = WEEKDAYS_KO[:len(visible_cols)]

    entries: List[Dict] = []
    for col_idx, td in enumerate(visible_cols):
        weekday = weekday_map[col_idx]
        # 같은 td 내부 기준 rect (상대 좌표계용)
        td_rect = _rect(driver, td)

        # 3) 그리드(시간 눈금) 분석 → px_per_hour 산출
        grids = []
        try:
            grids = td.find_elements(By.CSS_SELECTOR, ".grids .grid")
        except Exception:
            pass
        if len(grids) >= 2:
            y0 = _rect(driver, grids[0])["y"] - td_rect["y"]
            y1 = None
            # 서로 다른 y를 가진 첫 두 그리드로 간격 계산
            for g in grids[1:]:
                yg = _rect(driver, g)["y"] - td_rect["y"]
                if abs(yg - y0) > 0.5:
                    y1 = yg; break
            if y1 is None:
                px_per_hour = 50.0
                grid0 = 0.0
            else:
                px_per_hour = abs(y1 - y0)
                grid0 = min(y0, y1) if y0 >= 0 else 0.0
        else:
            # 폴백
            px_per_hour = 50.0
            grid0 = 0.0
        px_per_30 = px_per_hour / 2.0

        # 4) 과목 블록
        subjects = td.find_elements(By.CSS_SELECTOR, ".cols .subject")
        for sb in subjects:
            sb_rect = _rect(driver, sb)
            # 상대 y/height
            top_rel = sb_rect["y"] - td_rect["y"]
            h_rel = sb_rect["h"]

            # 시작/끝 시간 계산 (5분 단위 스냅)
            start_hours = (top_rel - grid0) / max(1.0, px_per_hour)
            dur_hours   = h_rel / max(1.0, px_per_hour)
            s_min = max(0, int(round(start_hours * 60 / 5.0) * 5))
            e_min = max(0, int(round((start_hours + dur_hours) * 60 / 5.0) * 5))

            sh, sm = divmod(s_min, 60)
            eh, em = divmod(e_min, 60)

            subj = _extract_subject(sb) or "미확인과목"

            entries.append({
                "subject": subj,
                "weekday_ko": weekday,
                "start": _to_hhmm(sh, sm),
                "end":   _to_hhmm(eh, em),
            })

    # 정렬/중복 제거
    order = {d:i for i,d in enumerate(WEEKDAYS_KO)}
    uniq, seen = [], set()
    for e in sorted(entries, key=lambda e:(order.get(e["weekday_ko"],99), e["start"], e["subject"])):
        k = (e["weekday_ko"], e["start"], e["end"], e["subject"])
        if k in seen: continue
        seen.add(k); uniq.append(e)
    return uniq

# ───────── 기존 dom/text/css 파서 (요약: 그대로 유지) ─────────
def _html_to_text(html: str) -> str:
    if not html: return ""
    s = re.sub(r'(?i)<\s*(br|/tr|/li|/p|/div|/h\d|/th|/td)\s*>', '\n', html)
    s = re.sub(r'(?i)<\s*(tr|li|p|div|h\d|th|td)\b[^>]*>', '\n', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = py_html.unescape(s)
    s = re.sub(r'[ \t\r\f]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n', s)
    return s

def _parse_dom_semantic(driver: webdriver.Chrome, *, url: str) -> List[Dict]:
    driver.get(url); _document_ready(driver, 12)
    selectors = [
        "[data-start]", "[data-begin]", "[data-time]", "[data-end]", "[data-day]",
        ".fc-event", ".rbc-event", ".tui-full-calendar-time-schedule",
        ".event", ".class", ".lesson", ".lecture", ".subject",
        "[aria-label]", "[role='gridcell'] [role='button']"
    ]
    cands = []
    for sel in selectors:
        try: cands.extend(driver.find_elements(By.CSS_SELECTOR, sel))
        except Exception: pass
    uniq, seen = [], set()
    def sig(el):
        try: t = (el.text or "").strip()
        except Exception: t = ""
        try: al = el.get_attribute("aria-label") or ""
        except Exception: al = ""
        try: dt = el.get_attribute("data-title") or ""
        except Exception: dt = ""
        return (t[:80], al[:80], dt[:80])
    for el in cands:
        key = sig(el)
        if key in seen: continue
        seen.add(key); uniq.append(el)
    cands = uniq[:800]

    header_days: List[Tuple[int,str]] = []
    try:
        hdrs = driver.find_elements(By.CSS_SELECTOR, "thead th, .fc-col-header th, .rbc-time-header, .days td, .tablehead td")
        for idx, h in enumerate(hdrs):
            wk = _weekday_from_text((h.text or "").strip())
            if wk: header_days.append((idx, wk))
    except Exception:
        pass

    def weekday_from_ancestors(el) -> Optional[str]:
        for attr in ["data-day","data-weekday","data-date","aria-label","title"]:
            try: v = el.get_attribute(attr) or ""
            except Exception: v = ""
            wk = _weekday_from_text(v)
            if wk: return wk
        try:
            parent = el.find_element(By.XPATH, "./ancestor::*[self::td or self::div or self::section][1]")
            wk = _weekday_from_text((parent.text or "")[:200])
            if wk: return wk
        except Exception:
            pass
        if header_days:
            try:
                td = el.find_element(By.XPATH, "./ancestor::td[1]")
                tr = td.find_element(By.XPATH, "./ancestor::tr[1]")
                tds = tr.find_elements(By.TAG_NAME, "td")
                idx = list(tds).index(td)
                for col_i, w in header_days:
                    if col_i == idx: return w
                if 0 <= idx < len(header_days): return header_days[idx][1]
            except Exception:
                pass
        return None

    entries: List[Dict] = []
    for el in cands:
        times_src = ""
        for attr in ["aria-label","data-time","data-start","data-begin","title"]:
            try: v = el.get_attribute(attr) or ""
            except Exception: v = ""
            if v and len(v) > len(times_src): times_src = v
        try: txt = el.text or ""
        except Exception: txt = ""
        if len(txt) > len(times_src): times_src = txt

        sh=sm=eh=em=None
        m = TIME_RANGE_RE.search(times_src.replace(" ","")) or TIME_RANGE_RE.search(times_src)
        if m:
            sh,sm,eh,em = m.group("s_h","s_m","e_h","e_m")
        else:
            mm = SINGLE_TIME_RE.findall(times_src)
            if len(mm) >= 2:
                (sh,sm),(eh,em) = mm[0], mm[1]

        wk = weekday_from_ancestors(el) or _weekday_from_text(times_src) or _weekday_from_text(txt)
        subj = _extract_subject(el)

        if subj and wk and None not in (sh,sm,eh,em):
            entries.append({
                "subject": subj,
                "weekday_ko": wk,
                "start": _to_hhmm(int(sh), int(sm)),
                "end":   _to_hhmm(int(eh), int(em)),
            })

    if entries:
        order = {d:i for i,d in enumerate(WEEKDAYS_KO)}
        uniq2, seen2 = [], set()
        for e in sorted(entries, key=lambda e:(order.get(e["weekday_ko"],99), e["start"], e["subject"])):
            k = (e["weekday_ko"], e["start"], e["end"], e["subject"])
            if k in seen2: continue
            seen2.add(k); uniq2.append(e)
        return uniq2
    return []

def _parse_textual(driver: webdriver.Chrome, *, url: str) -> List[Dict]:
    driver.get(url); _document_ready(driver, 10)
    text = _html_to_text(driver.page_source or "")
    entries: List[Dict] = []
    for m in TIME_RANGE_RE.finditer(text):
        sh,sm,eh,em = m.group("s_h","s_m","e_h","e_m")
        s_idx,e_idx = m.span()
        ctx = text[max(0,s_idx-160):min(len(text),e_idx+160)]
        wk = _weekday_from_text(ctx) or _weekday_from_text(text[max(0,s_idx-400):min(len(text),e_idx+400)])
        if not wk: continue
        subj = _clean_subject_from_text(ctx) or _clean_subject_from_text(text[max(0,s_idx-240):min(len(text),e_idx+240)])
        if not subj: continue
        entries.append({
            "subject": subj, "weekday_ko": wk,
            "start": _to_hhmm(int(sh), int(sm)), "end": _to_hhmm(int(eh), int(em))
        })
        if len(entries) >= 200: break
    if entries:
        order = {d:i for i,d in enumerate(WEEKDAYS_KO)}
        uniq, seen = [], set()
        for e in sorted(entries, key=lambda e:(order.get(e["weekday_ko"],99), e["start"], e["subject"])):
            k = (e["weekday_ko"], e["start"], e["end"], e["subject"])
            if k in seen: continue
            seen.add(k); uniq.append(e)
        return uniq
    return []

def _parse_css_positioned(
    driver: webdriver.Chrome, *, url: str,
    start_hour: int = 9, px_per_30: float = 40.33, top_offset: float = 540.0, # 기본값 수정
    head_selector: str = "", body_selector: str = "", block_selector: str = "", timeout: int = 20
) -> List[Dict]:
    driver.get(url); _document_ready(driver, timeout)
    def _split(sel: str) -> List[str]:
        return [p.strip() for p in (sel or "").split(",") if p.strip()]
    heads = _split(head_selector); bodys = _split(body_selector); blocks_sel = _split(block_selector)

    # body
    found_body = None
    for sel in bodys:
        try:
            found_body = driver.find_element(By.CSS_SELECTOR, sel); break
        except Exception: continue
    if not found_body:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, block_selector)
            if elems:
                found_body = elems[0].find_element(By.XPATH, "./ancestor::*[1]")
        except Exception:
            pass
    if not found_body:
        raise RuntimeError("본문 컨테이너를 찾지 못했습니다.")

    # header days
    days = []
    for sel in heads:
        try:
            for td in driver.find_elements(By.CSS_SELECTOR, sel):
                wk = _weekday_from_text((td.text or "").strip())
                if wk: days.append(wk)
        except Exception: pass
    if days:
        seen=set(); days=[d for d in days if not (d in seen or seen.add(d))]

    elems = []
    for sel in blocks_sel:
        try: elems.extend(driver.find_elements(By.CSS_SELECTOR, sel))
        except Exception: pass
    if not elems:
        try: elems = driver.find_elements(By.CSS_SELECTOR, "*[style]")
        except Exception: elems = []
    if not elems:
        raise RuntimeError("강의 블록을 찾지 못했습니다.")

    try: body_rect = found_body.rect
    except Exception:
        body_rect = {"x":0,"y":0,"width":driver.execute_script("return document.body.clientWidth||0;"),"height":0}

    order = {d:i for i,d in enumerate(WEEKDAYS_KO)}
    results: List[Dict] = []

    for el in elems:
        style = el.get_attribute("style") or ""
        hm = re.search(r'height:\s*(-?\d+(?:\.\d+)?)px', style)
        tm = re.search(r'top:\s*(-?\d+(?:\.\d+)?)px', style)
        if not (hm and tm):
            try:
                comp = driver.execute_script(
                    "const s = window.getComputedStyle(arguments[0]);"
                    "return {h:s.getPropertyValue('height'), t:s.getPropertyValue('top')};", el)
                h = comp.get("h"); t = comp.get("t")
                hm = re.search(r"(-?\d+(?:\.\d+)?)px", h or "")
                tm = re.search(r"(-?\d+(?:\.\d+)?)px", t or "")
            except Exception:
                hm = tm = None
        if not (hm and tm): continue
        h = float(hm.group(1)); t = float(tm.group(1))

        # 요일: 열 인덱스 추정
        day = ""
        try:
            parent_td = el.find_element(By.XPATH, "./ancestor::td")
            tr = parent_td.find_element(By.XPATH, "./ancestor::tr")
            tds = tr.find_elements(By.TAG_NAME, "td")
            td_idx = list(tds).index(parent_td)
            if days and td_idx < len(days):
                day = days[td_idx]
            else:
                if 0 <= td_idx < len(WEEKDAYS_KO): day = WEEKDAYS_KO[td_idx]
        except Exception:
            pass
        subj = _extract_subject(el) or "미확인과목"

        base = (start_hour or 0) * 60
        start_idx = (t - (top_offset or 0)) / (px_per_30 or 25)
        start_minutes = max(0, int(round(start_idx * 30)))
        dur_idx = (h - 1) / (px_per_30 or 25)
        duration_min = max(30, int(round(dur_idx * 30)))
        s_total = base + start_minutes
        e_total = s_total + duration_min

        results.append({
            "subject": subj,
            "weekday_ko": day or "월",
            "start": _to_hhmm(s_total//60, s_total%60),
            "end":   _to_hhmm(e_total//60, e_total%60),
        })

    uniq, seen = [], set()
    for e in sorted(results, key=lambda e:(order.get(e["weekday_ko"],99), e["start"], e["subject"])):
        k = (e["weekday_ko"], e["start"], e["end"], e["subject"])
        if k in seen: continue
        seen.add(k); uniq.append(e)
    return uniq

# ───────── Public API ─────────
def parse_schedule_from_web(
    url: str,
    *,
    mode: str = "auto",                  # "auto" | "kor" | "dom" | "text" | "css"
    start_hour: Optional[int] = 9,      # css
    px_per_30: Optional[float] = 40.33,   # css
    top_offset: Optional[float] = 540.0,   # css
    timeout: int = 30,
    head_selector: str = ".tablehead td,.fc-col-header th,.header td,thead th,.days td,.fc-col-header-cell,.rbc-time-header,.tui-full-calendar-dayname",
    body_selector: str = ".tablebody,.fc-timegrid,.timetable,.timeTable,.schedule-body,.weekly-schedule,.calendar,.fc-scroller-harness,.rbc-time-content,.rbc-time-view,.tui-full-calendar-timegrid-container,.timeGrid,.schedule",
    block_selector: str = ".subject,.fc-timegrid-event,.fc-event,.lesson,.class,.event,.lecture,.rbc-event,.tui-full-calendar-time-schedule,[data-event],[class*='event']",
    interactive_login: bool = False,
    wait_login_seconds: int = 120,
) -> List[Dict]:
    if ("everytime.kr" in url.lower()) and ("/timetable" in url.lower()) and not interactive_login:
        # 에브리타임 공유 시간표 URL을 위한 모드 강제 변경
        mode = "css" 
        
    driver = _get_driver(headless=(mode not in ("dom","text","kor") and not interactive_login))

    def run_kor() -> List[Dict]:
        try: return _parse_kor_table_layout(driver, url=url)
        except Exception: return []

    def run_dom() -> List[Dict]:
        try: return _parse_dom_semantic(driver, url=url)
        except Exception: return []

    def run_text() -> List[Dict]:
        try: return _parse_textual(driver, url=url)
        except Exception: return []

    def run_css() -> List[Dict]:
        try:
            return _parse_css_positioned(
                driver, url=url,
                start_hour=start_hour or 9,
                px_per_30=px_per_30 or 25,
                top_offset=top_offset or 450,
                head_selector=head_selector,
                body_selector=body_selector,
                block_selector=block_selector,
                timeout=timeout
            )
        except Exception: return []

    if mode == "kor":
        res = run_kor()
        if not res: raise RuntimeError("KOR 레이아웃 파싱 실패(해당 구조가 아님).")
        return res
    if mode == "dom":
        res = run_dom()
        if not res: raise RuntimeError("DOM 기반 파싱 실패.")
        return res
    if mode == "text":
        res = run_text()
        if not res: raise RuntimeError("TEXT 기반 파싱 실패.")
        return res
    if mode == "css":
        res = run_css()
        if not res: raise RuntimeError("CSS 기반 파싱 실패.")
        return res

    # auto: kor → dom → text → css
    for fn in (run_kor, run_dom, run_text, run_css):
        r = fn()
        if r: return r
    raise RuntimeError("파싱 실패(KOR/DOM/TEXT/CSS 모두 실패). URL/로그인 여부를 확인하세요.")

def diagnose_schedule_page(
    url: str,
    *,
    max_samples: int = 20,
    for_mode: str = "auto"
) -> Dict:
    driver = _get_driver(headless=False)
    driver.get(url)
    _document_ready(driver, 10)

    info: Dict = {"url": url, "title": driver.title, "mode_hint": for_mode}

    # kor 레이아웃 힌트
    try:
        info["kor_layout"] = _is_kor_table_layout(driver)
        if info["kor_layout"]:
            th_times = driver.find_element(By.CSS_SELECTOR, "th .times")
            tr = th_times.find_element(By.XPATH, "./ancestor::tr[1]")
            tds = tr.find_elements(By.TAG_NAME, "td")
            visible = []
            for td in tds:
                style = (td.get_attribute("style") or "").replace(" ", "").lower()
                if "display:none" not in style: visible.append(td)
            info["kor_visible_cols"] = len(visible)
            if visible:
                td0 = visible[0]
                td_rect = _rect(driver, td0)
                grids = td0.find_elements(By.CSS_SELECTOR, ".grids .grid")
                if len(grids) >= 2:
                    y = [_rect(driver, g)["y"] - td_rect["y"] for g in grids[:3]]
                    diffs = [abs(y[i+1]-y[i]) for i in range(len(y)-1) if abs(y[i+1]-y[i])>0.5]
                    info["kor_px_per_hour"] = (sum(diffs)/len(diffs)) if diffs else None
                else:
                    info["kor_px_per_hour"] = None
    except Exception as e:
        info["kor_error"] = str(e)

    # dom 샘플
    try:
        selectors = [
            "[data-start]", "[data-begin]", "[data-time]", "[data-end]", "[data-day]",
            ".fc-event", ".rbc-event", ".tui-full-calendar-time-schedule",
            ".event", ".class", ".lesson", ".lecture", ".subject",
            "[aria-label]", "[role='gridcell'] [role='button']"
        ]
        cands = []
        for sel in selectors:
            try: cands.extend(driver.find_elements(By.CSS_SELECTOR, sel))
            except Exception: pass
        samples = []
        for el in cands[:max_samples]:
            samples.append({
                "text": (el.text or ""),
                "aria": el.get_attribute("aria-label") or "",
                "title": el.get_attribute("title") or "",
                "data-title": el.get_attribute("data-title") or "",
                "data-time": el.get_attribute("data-time") or "",
                "data-start": el.get_attribute("data-start") or "",
                "data-end": el.get_attribute("data-end") or "",
                "data-day": el.get_attribute("data-day") or "",
                "style": el.get_attribute("style") or ""
            })
        info["dom_samples"] = samples
    except Exception as e:
        info["dom_samples_error"] = str(e)

    # text 통계
    try:
        text = _html_to_text(driver.page_source or "")
        times = list(TIME_RANGE_RE.finditer(text))
        info["text_regex_time_count"] = len(times)
        wd_counts = {}
        for token in (WEEKDAY_KO_FULL + WEEKDAYS_KO + WEEKDAY_EN_FULL + WEEKDAY_EN):
            c = text.lower().count(token.lower())
            if c: wd_counts[token] = c
        info["text_weekday_counts"] = wd_counts
        info["text_excerpt"] = text[:800]
    except Exception as e:
        info["text_error"] = str(e)

    return info

if __name__ == '__main__':
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python webscrape.py <url> [mode] [login_wait_seconds]")
        sys.exit(1)
    url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    login_wait = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    interactive = login_wait > 0

    if mode == "diagnose":
        result = diagnose_schedule_page(url)
    else:
        result = parse_schedule_from_web(
            url,
            mode=mode,
            interactive_login=interactive,
            wait_login_seconds=login_wait
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
