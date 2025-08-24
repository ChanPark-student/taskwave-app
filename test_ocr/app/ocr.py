# app/ocr.py
from __future__ import annotations
import os, re, math
from typing import List, Tuple, Dict, Any
import numpy as np
import cv2
import pytesseract
import pandas as pd

# ---- Tesseract 실행 파일 경로(윈도우 지원)
TESSERACT_CMD = os.environ.get("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

WEEKDAYS_KO = ["월","화","수","목","금","토","일"]
WEEKDAYS_EN = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# =========================
# 기본 유틸
# =========================
def _read_image_from_bytes(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")
    return img

def _upsample_and_binarize(img: np.ndarray) -> np.ndarray:
    """OCR 안정화를 위해 업샘플 + 이진화."""
    h, w = img.shape[:2]
    scale = 1.7 if max(h, w) < 2200 else 1.25
    up = cv2.resize(img, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    g = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    g = cv2.bilateralFilter(g, 11, 90, 90)
    th = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 31, 7)
    return th

def _tesseract_df(img_bin: np.ndarray, lang="kor+eng", psm:int=6) -> pd.DataFrame:
    """Tesseract TSV → pandas DataFrame."""
    custom = f"--oem 3 --psm {psm}"
    df = pytesseract.image_to_data(img_bin, lang=lang, config=custom, output_type=pytesseract.Output.DATAFRAME)
    if df is None or len(df)==0:
        return pd.DataFrame(columns=['text','conf','left','top','width','height'])
    # 타입 정리
    df['conf'] = pd.to_numeric(df['conf'], errors='coerce')
    df = df.dropna(subset=['conf'])
    df = df[df['conf'] >= 30]
    if 'text' in df.columns:
        df['text'] = df['text'].astype(str).fillna('').str.strip()
    else:
        df['text'] = ''
    df = df[df['text'] != '']
    # 기하 속성
    df['cx'] = df['left'] + df['width']/2.0
    df['cy'] = df['top'] + df['height']/2.0
    df['right'] = df['left'] + df['width']
    df['bottom'] = df['top'] + df['height']
    return df

# =========================
# 요일/시간축 탐지
# =========================
_TIME_PAT_AMPM = re.compile(r'(오전|오후)\s*(\d{1,2})\s*시')
_TIME_PAT_HHMM = re.compile(r'\b([01]?\d|2[0-3]):([0-5]\d)\b')
_TIME_PAT_HH   = re.compile(r'\b(\d{1,2})\s*시\b')

def _find_weekday_columns(df: pd.DataFrame, img_w: int, img_h:int) -> tuple[Dict[str,float], float]:
    """상단 밴드에서 요일 헤더 위치(x-center) 추출. 실패 시 월~금 균등분할 폴백."""
    top_band = img_h * 0.20
    cand = []
    for _, r in df.iterrows():
        if r['cy'] > top_band:
            continue
        t = r['text']
        found = False
        for ko in WEEKDAYS_KO:
            if t == ko or t.startswith(ko):
                cand.append((ko, float(r['cx']), float(r['cy']))); found=True; break
        if found: 
            continue
        for idx, en in enumerate(WEEKDAYS_EN):
            if t.lower().startswith(en.lower()):
                cand.append((WEEKDAYS_KO[idx], float(r['cx']), float(r['cy']))); break

    colmap: Dict[str,float] = {}
    header_y = 0.0
    for wd in WEEKDAYS_KO:
        ys = [(cx, cy) for (w, cx, cy) in cand if w == wd]
        if ys:
            cx, cy = sorted(ys, key=lambda x: x[1])[0]   # 가장 위의 것
            colmap[wd] = cx
            header_y = max(header_y, cy)

    # 5개 미만이면 월~금 균등분할 폴백(탐지 실패시만)
    if len([k for k in colmap.keys() if k in WEEKDAYS_KO[:5]]) < 5:
        cols = 5
        step = img_w / cols
        colmap = {WEEKDAYS_KO[i]: (i+0.5)*step for i in range(cols)}

    return dict(sorted(colmap.items(), key=lambda kv: kv[1])), float(header_y)

def _parse_korean_time(s: str) -> str | None:
    s0 = s.replace(" ", "")
    m = _TIME_PAT_AMPM.search(s0)
    if m:
        ap, h = m.group(1), int(m.group(2))
        h = (0 if h == 12 else h) if ap == "오전" else (12 if h == 12 else h+12)
        return f"{h:02d}:00"
    m = _TIME_PAT_HHMM.search(s0)
    if m:
        return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
    m = _TIME_PAT_HH.search(s0)
    if m:
        h = int(m.group(1))
        if 0 <= h <= 23:
            return f"{h:02d}:00"
    return None

def _find_time_rows(df: pd.DataFrame, img_h: int, img_w:int, header_y: float) -> List[Tuple[float, str]]:
    """왼쪽 24% 영역 + 헤더 아래에서만 시간 라벨 수집. 부족하면 09~18 폴백."""
    left_zone = img_w * 0.24
    times: List[Tuple[float,str]] = []
    for _, r in df.iterrows():
        if r['cx'] > left_zone or r['cy'] < header_y + 8:
            continue
        parsed = _parse_korean_time(r['text'])
        if parsed:
            times.append((float(r['cy']), parsed))

    times.sort(key=lambda x: x[0])
    # y-근접 병합(<=18px)
    merged: List[Tuple[float,str]] = []
    for y, hhmm in times:
        if not merged:
            merged.append((y, hhmm)); continue
        py, _ = merged[-1]
        if abs(y - py) <= 18:
            if y < py:
                merged[-1] = (y, hhmm)
        else:
            merged.append((y, hhmm))

    # 폴백: 09~18 균등 eye-lines
    if len(merged) < 3:
        top = max(header_y + 30, img_h*0.12)
        bottom = img_h * 0.95
        steps = 10  # 09..18
        ys = np.linspace(top, bottom, steps)
        merged = [(float(ys[i]), f"{9+i:02d}:00") for i in range(steps)]
    return merged

# =========================
# 과목 블록(색상 기반) 탐지 + 세로 분할
# =========================
def _colored_mask(img: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, _ = cv2.split(hsv)
    _, sbin = cv2.threshold(s, 28, 255, cv2.THRESH_BINARY)
    k1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    k2 = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    mask = cv2.morphologyEx(sbin, cv2.MORPH_OPEN, k1, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k2, iterations=1)
    return mask

def _split_by_horizontal_gaps(mask_roi: np.ndarray, x:int, y:int) -> List[Tuple[int,int,int,int]]:
    """ROI 내 행 방향 투영으로 빈 영역 기준 세로 분할."""
    h, w = mask_roi.shape[:2]
    if h == 0 or w == 0:
        return []
    proj = (mask_roi > 0).sum(axis=1)
    if proj.size == 0 or proj.max() == 0:
        return []
    thr = max(3, int(0.10 * proj.max()))
    on = proj >= thr
    rects = []
    i = 0
    while i < h:
        while i < h and not on[i]:
            i += 1
        if i >= h: break
        start = i
        while i < h and on[i]:
            i += 1
        end = i
        band_h = end - start
        if band_h >= max(18, int(0.04*h)):
            rects.append((x, y + start, w, band_h))
    return rects

def _iou(a,b):
    ax,ay,aw,ah = a; bx,by,bw,bh = b
    x1=max(ax,bx); y1=max(ay,by); x2=min(ax+aw,bx+bw); y2=min(ay+ah,bx+bh)
    if x2<=x1 or y2<=y1: return 0.0
    inter=(x2-x1)*(y2-y1)
    union=aw*ah + bw*bh - inter
    return inter/union

def _find_subject_blocks(img: np.ndarray) -> List[Tuple[int,int,int,int]]:
    mask = _colored_mask(img)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = img.shape[:2]
    raw: List[Tuple[int,int,int,int]] = []
    for c in contours:
        x,y,w,h = cv2.boundingRect(c)
        if w*h < (W*H)*0.002:
            continue
        if y < H*0.08 and h < H*0.15:
            continue
        raw.append((x,y,w,h))

    # IoU 병합(겹치는 것만)
    blocks: List[Tuple[int,int,int,int]] = []
    for r in sorted(raw, key=lambda b: (b[1], b[0])):
        merged=False
        for i,b in enumerate(blocks):
            if _iou(r,b) > 0.3:
                x=min(r[0],b[0]); y=min(r[1],b[1])
                xe=max(r[0]+r[2], b[0]+b[2]); ye=max(r[1]+r[3], b[1]+b[3])
                blocks[i]=(x,y,xe-x,ye-y); merged=True; break
        if not merged:
            blocks.append(r)

    # 세로 스택 분할
    final_blocks: List[Tuple[int,int,int,int]] = []
    for (x,y,w,h) in blocks:
        roi = mask[y:y+h, x:x+w]
        sub = _split_by_horizontal_gaps(roi, x, y)
        if sub:
            final_blocks.extend(sub)
        else:
            final_blocks.append((x,y,w,h))
    return final_blocks

# =========================
# 블록 내부 OCR & 라인 그룹
# =========================
def _ocr_tokens_in_rect(img_bin: np.ndarray, rect) -> pd.DataFrame:
    """사각형 ROI에서 토큰 단위 OCR (psm6+psm7)."""
    x,y,w,h = rect
    pad = max(2, int(min(w,h)*0.05))
    x1 = max(0, x - pad); y1 = max(0, y - pad)
    x2 = min(img_bin.shape[1], x + w + pad)
    y2 = min(img_bin.shape[0], y + h + pad)
    crop = img_bin[y1:y2, x1:x2]

    df1 = _tesseract_df(crop, psm=6)
    df2 = _tesseract_df(crop, psm=7)
    df = pd.concat([df1, df2], ignore_index=True)
    if df.empty:
        return df

    # 원래 좌표계로 복구
    df['left']   = df['left']   + x1
    df['top']    = df['top']    + y1
    df['right']  = df['right']  + x1
    df['bottom'] = df['bottom'] + y1
    df['cx']     = df['left'] + (df['right']-df['left'])/2.0
    df['cy']     = df['top']  + (df['bottom']-df['top'])/2.0
    return df

def _group_lines(df_tokens: pd.DataFrame) -> List[Tuple[str, float]]:
    """토큰 DF를 y-근접(<=18px)으로 묶어 줄 텍스트 생성. (text, line_center_y)"""
    if df_tokens.empty:
        return []
    rows = df_tokens.sort_values(['cy','cx']).to_dict('records')
    lines, cur, py = [], [], None
    for r in rows:
        if py is None or abs(r['cy']-py) <= 18:
            cur.append(r)
        else:
            lines.append(cur); cur=[r]
        py = r['cy']
    if cur: lines.append(cur)
    out = []
    for grp in lines:
        grp_sorted = sorted(grp, key=lambda t: t['cx'])
        txt = " ".join(g['text'] for g in grp_sorted).strip()
        y_center = float(np.mean([g['cy'] for g in grp_sorted]))
        out.append((txt, y_center))
    return out

# =========================
# 제목/교수/강의실 추출 (형태/위치 기반)
# =========================
# 강의실 패턴: "문자+숫자" 조합 또는 '공xx-xxx'만 허용(순수 숫자 금지)
ROOM_PATS = [
    re.compile(r'\b([A-Za-z]{1,4}[0-9A-Za-z]{0,3}-?\d{2,4})\b'),  # S1A-520, B-312, S1A312
    re.compile(r'(공\s?\d{1,2}[A-Za-z]?[-–]?\d{2,4})')            # 공14-519, 공1A-312
]

def _line_is_room_like(s: str) -> bool:
    compact = s.replace(" ", "")
    for pat in ROOM_PATS:
        if pat.search(compact):
            return True
    # 숫자/하이픈이 많으면 방 가능성↑
    digits = sum(ch.isdigit() for ch in compact)
    hy = compact.count('-') + compact.count('–')
    if digits >= 3 and hy >= 1:
        return True
    return False

def _hangul_ratio(s: str) -> float:
    if not s: return 0.0
    clean = re.sub(r'[^0-9A-Za-z가-힣()\[\]\- ]', '', s)
    total = max(1, len(clean))
    k = sum(1 for ch in clean if '\uac00' <= ch <= '\ud7a3')
    return k/total

def _longest_hangul_run(s: str) -> int:
    """가장 긴 연속 한글 길이(제목 판단에 가산점)."""
    mlen = 0; cur = 0
    for ch in s:
        if '\uac00' <= ch <= '\ud7a3':
            cur += 1; mlen = max(mlen, cur)
        else:
            cur = 0
    return mlen

def _compact_korean(s: str) -> str:
    """한글 사이 공백 제거: '휴 공 학 먼 인' → '휴공학먼인'."""
    return re.sub(r'(?<=[\uac00-\ud7a3])\s+(?=[\uac00-\ud7a3])', '', s)

def _choose_title_prof_room(tokens_df: pd.DataFrame, lines: List[Tuple[str,float]], rect: Tuple[int,int,int,int]) -> Tuple[str, str|None, str|None, str]:
    # 0) 라인 전처리: 공백 정규화 + 한글 붙이기
    cleaned_lines: List[Tuple[str,float]] = []
    for txt, y in lines:
        t = re.sub(r'\s+', ' ', txt).strip()
        t = _compact_korean(t)
        if t:
            cleaned_lines.append((t, y))

    joined_raw = "\n".join([t for t,_ in cleaned_lines]) if cleaned_lines else ""

    # 1) 강의실
    room = None
    compact_all = joined_raw.replace(" ", "")
    for pat in ROOM_PATS:
        m = pat.search(compact_all)
        if m:
            room = m.group(1)
            break

    # 2) 제목 스코어: 한글연속길이↑, 한글비율↑, 길이↑, 숫자↓, 방형식/앞뒤문장부호 패널티
    def title_score(s: str) -> Tuple[int,int,int,int]:
        clean = re.sub(r'\s+', ' ', s).strip()
        if not clean:
            return (-10, -10, -10, -10)
        if _line_is_room_like(clean):
            return (-1000, -1000, -1000, -1000)
        leading_punct = 1 if re.match(r'^[^\w\uac00-\ud7a3]+', clean) else 0
        trailing_punct = 1 if re.search(r'[^\w\uac00-\ud7a3]+$', clean) else 0
        hr = int(_hangul_ratio(clean)*100)
        run = _longest_hangul_run(clean)
        num_pen = -sum(ch.isdigit() for ch in clean)
        length = len(clean)
        return (run*3 + hr - (leading_punct+trailing_punct)*5, length, num_pen, hr)

    title_line = ""
    if cleaned_lines:
        title_line = max([t for t,_ in cleaned_lines], key=title_score)
    title_line = title_line.strip()

    # 3) 교수: 블록 하단 40% 안쪽 라인에서, 순수 한글 2~4자 토큰
    prof = None
    if not tokens_df.empty:
        x,y,w,h = rect
        cutoff = y + h*0.60   # 하단 40%
        cand = tokens_df[(tokens_df['cy'] >= cutoff)]
        names = []
        for _, r in cand.iterrows():
            t = re.sub(r'[^가-힣]', '', str(r['text']))
            if 2 <= len(t) <= 4:
                names.append((t, r['cy'], r['conf']))
        names = [n for n in names if n[0] and n[0] not in title_line]
        if names:
            def ns(n):
                name, cy, conf = n
                return (conf, cy, 1 if len(name)>=3 else 0)
            prof = sorted(names, key=ns, reverse=True)[0][0]

    return title_line, prof, room, joined_raw

# =========================
# 라인 갭 기반 서브블록 분할 (텍스트 기준)
# =========================
def _split_rect_by_line_gaps(rect: Tuple[int,int,int,int], lines: List[Tuple[str,float]], tokens_df: pd.DataFrame) -> List[Tuple[int,int,int,int]]:
    """블록 내부 라인들의 y 간격으로 큰 간격이 있으면 안전하게 서브블록으로 분할."""
    if len(lines) <= 1:
        return [rect]
    ys = sorted([y for _,y in lines])
    gaps = np.diff(ys)
    if len(gaps) == 0:
        return [rect]
    med_gap = np.median(gaps)
    # 라인 높이(문자 높이) 추정 → 패딩 결정
    if not tokens_df.empty:
        line_heights = (tokens_df['bottom'] - tokens_df['top']).to_numpy()
        med_h = float(np.median(line_heights)) if len(line_heights) else 14.0
    else:
        med_h = 14.0
    # 큰 간격 기준
    thr = max(22.0, 1.6 * float(med_gap))
    splits = []
    start_y = ys[0]
    for i, g in enumerate(gaps):
        if g > thr:
            splits.append((start_y, ys[i]))
            start_y = ys[i+1]
    splits.append((start_y, ys[-1]))

    x,y,w,h = rect
    out = []
    for (sy, ey) in splits:
        top = int(max(y, sy - med_h*0.8))
        bot = int(min(y + h, ey + med_h*0.8))
        if bot - top >= max(20, int(med_h*1.2)):
            out.append((x, top, w, bot - top))
    # 분할 결과가 너무 잘게 쪼개지면 원본 유지
    if len(out) == 0:
        return [rect]
    return out

# =========================
# 시간 매핑
# =========================
def _map_rect_to_time(rect, time_rows: List[Tuple[float,str]], img_h: int, header_y: float) -> Tuple[str,str]:
    x,y,w,h = rect
    top = y; bottom = y+h
    times_y = [ty for ty,_ in time_rows]
    if not times_y:
        start_base = 9; step = (img_h - header_y)/9.0
        s_idx = max(0, min(8, int((top-header_y)/step)))
        e_idx = max(s_idx+1, min(9, int(math.ceil((bottom-header_y)/step))))
        return f"{start_base+s_idx:02d}:00", f"{start_base+e_idx:02d}:00"

    above = [i for i,ty in enumerate(times_y) if ty <= top]
    below = [i for i,ty in enumerate(times_y) if ty >= bottom]
    s_i = max(above) if above else 0
    e_i = (min(below) + 1) if below else len(time_rows)
    s_i = max(0, min(s_i, len(time_rows)-1))
    e_i = max(s_i+1, min(e_i, len(time_rows)))
    s_time = time_rows[s_i][1]
    # 1칸=1시간 가정
    sh = int(s_time[:2]); sm = int(s_time[3:5])
    e_steps = e_i - s_i
    eh = (sh + e_steps) % 24
    e_time = f"{eh:02d}:{sm:02d}"
    return s_time, e_time

# =========================
# 메인 파이프라인
# =========================
def parse_timetable(image_bytes: bytes) -> Dict[str, Any]:
    img = _read_image_from_bytes(image_bytes)
    H, W = img.shape[:2]

    img_bin = _upsample_and_binarize(img)
    df_all = _tesseract_df(img_bin, psm=6)

    # 컬럼/시간축
    colmap, header_y = _find_weekday_columns(df_all, W, H)
    time_rows = _find_time_rows(df_all, H, W, header_y)

    # 과목 블록(색상)
    rects = _find_subject_blocks(img)
    # 폴백: 색 블록이 전혀 없을 때 텍스트 밀집 클러스터
    if not rects and not df_all.empty:
        try:
            from sklearn.cluster import DBSCAN
            pts = df_all[['cx','cy']].to_numpy()
            labels = DBSCAN(eps=38, min_samples=10).fit_predict(pts)
            df_all['cluster'] = labels
            for cid in sorted([c for c in set(labels) if c != -1]):
                sub = df_all[df_all['cluster']==cid]
                x1, y1 = int(sub['left'].min()), int(sub['top'].min())
                x2, y2 = int(sub['right'].max()), int(sub['bottom'].max())
                rects.append((x1,y1,x2-x1,y2-y1))
        except Exception:
            pass

    day_items = sorted(colmap.items(), key=lambda kv: kv[1])
    day_centers = [cx for _,cx in day_items]
    day_labels  = [wd for wd,_ in day_items]

    slots = []
    for rect in rects:
        # 1) 1차 OCR → 라인 추출
        tokens_df = _ocr_tokens_in_rect(img_bin, rect)
        if tokens_df.empty:
            continue
        lines = _group_lines(tokens_df)
        if not lines:
            continue

        # 2) 텍스트 간격 기반 서브블록 분할 (시간 정밀도 개선)
        sub_rects = _split_rect_by_line_gaps(rect, lines, tokens_df)

        for sub in sub_rects:
            sub_tokens = _ocr_tokens_in_rect(img_bin, sub)
            if sub_tokens.empty:
                continue
            sub_lines = _group_lines(sub_tokens)
            if not sub_lines:
                continue

            title, prof, room, raw = _choose_title_prof_room(sub_tokens, sub_lines, sub)

            # 요일 매핑
            sx,sy,sw,sh = sub
            cxx = sx + sw/2.0
            if day_centers:
                di = int(np.argmin(np.abs(np.array(day_centers) - cxx)))
                weekday = day_labels[di]
            else:
                weekday = WEEKDAYS_KO[0]

            # 시간 매핑
            start_time, end_time = _map_rect_to_time(sub, time_rows, H, header_y)

            slots.append({
                "weekday": weekday,
                "start_time": start_time,
                "end_time": end_time,
                "title": title,
                "professor": prof,
                "location": room,
                "raw_text": raw
            })

    # 정렬
    wd_order = {w:i for i,w in enumerate(WEEKDAYS_KO)}
    slots.sort(key=lambda s: (wd_order.get(s['weekday'], 99), s['start_time'], s['end_time'], s['title']))

    debug = {
        "weekday_columns": colmap,
        "time_rows": time_rows,
        "num_rects": len(rects),
        "ocr_tokens": int(len(df_all))
    }
    return {"count": len(slots), "slots": slots, "debug": debug}
