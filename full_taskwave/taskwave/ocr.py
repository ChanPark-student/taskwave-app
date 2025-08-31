from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import os, re, math

import numpy as np
import cv2
import pytesseract
from PIL import Image

# PDF -> 이미지
try:
    import fitz  # PyMuPDF
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# ---- Tesseract 경로(옵션) ----
# Windows에 Tesseract가 설치되어 있으면 보통 아래 경로에 있음.
_CANDIDATES = [
    os.environ.get("TESSERACT_CMD"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
for _p in _CANDIDATES:
    if _p and os.path.isfile(_p):
        pytesseract.pytesseract.tesseract_cmd = _p
        break

WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]
FULL_WEEKDAYS_KO = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

ROOM_RE = re.compile(
    r"(?:[가-힣A-Za-z]{1,4}\s?\d{1,3}[A-Za-z]?\s*[-–]?\s?\d{2,4}\b)"
    r"|(?:\b\d{2,3}\s*[-–]\s*\d{2,4}\b)"
    r"|(?:\b[A-Za-z]{1,3}\d{2,4}\b)",
    flags=re.IGNORECASE
)
NAME_RE = re.compile(r'^[가-힣]{2,4}$')
ONLY_KO = re.compile(r"[가-힣]+")

# -------------------- 이미지/페이지 로딩 --------------------
def _imread(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")

def _pdf_to_images(path: Path) -> List[Image.Image]:
    if not HAS_PDF:
        raise RuntimeError("PyMuPDF가 설치되어 있지 않아 PDF를 처리할 수 없습니다.")
    out = []
    with fitz.open(str(path)) as doc:
        for p in doc:
            pix = p.get_pixmap(dpi=220)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            out.append(img)
    return out

# -------------------- 전처리/격자 검출 --------------------
def _binarize(rgb: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.bilateralFilter(g, 7, 60, 60)
    return cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

def _detect_grid(binary: np.ndarray) -> Tuple[List[int], List[int]]:
    H, W = binary.shape[:2]
    work = cv2.medianBlur(binary, 3)

    # 수평/수직 선 분리
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(25, int(W*0.03)), 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(25, int(H*0.03))))
    h_img = cv2.morphologyEx(work, cv2.MORPH_OPEN, h_kernel, iterations=1)
    v_img = cv2.morphologyEx(work, cv2.MORPH_OPEN, v_kernel, iterations=1)

    # 라인 위치 후보
    y_pos = np.where(h_img.sum(axis=1) > 255 * max(8, int(W*0.02)))[0]
    x_pos = np.where(v_img.sum(axis=0) > 255 * max(8, int(H*0.02)))[0]

    def _group(pos, gap):  # 가까운 것 묶어 중앙값
        if len(pos) == 0: return []
        pos = np.sort(pos)
        groups, cur = [], [pos[0]]
        for p in pos[1:]:
            if p - cur[-1] <= gap: cur.append(p)
            else: groups.append(int(np.median(cur))); cur = [p]
        groups.append(int(np.median(cur)))
        return groups

    y_lines = _group(y_pos, gap=12)
    x_lines = _group(x_pos, gap=18)
    return y_lines, x_lines

def _edges_from_lines(lines: List[int], whole: int) -> List[int]:
    if not lines:
        return [0, whole]
    lines = sorted(lines)
    edges = [0]
    for a, b in zip(lines, lines[1:]):
        edges.append((a + b) // 2)
    edges.append(whole)
    return edges

# -------------------- OCR 편의 --------------------
def _ocr(img: np.ndarray | Image.Image, psm: int, lang="kor+eng") -> str:
    im = img if isinstance(img, Image.Image) else Image.fromarray(img)
    cfg = f"--psm {psm} --oem 1 -c preserve_interword_spaces=1"
    return pytesseract.image_to_string(im, lang=lang, config=cfg)

def _ocr_data(img: np.ndarray | Image.Image, psm: int = 6, lang="kor+eng"):
    im = img if isinstance(img, Image.Image) else Image.fromarray(img)
    cfg = f"--psm {psm} -c preserve_interword_spaces=1"
    df = pytesseract.image_to_data(im, lang=lang, config=cfg,
                                   output_type=pytesseract.Output.DATAFRAME)
    df = df.dropna(subset=["text"])
    rows = []
    for _, r in df.iterrows():
        t = str(r["text"]).strip()
        if not t: continue
        rows.append({
            "text": t,
            "left": int(r["left"]), "top": int(r["top"]),
            "width": int(r["width"]), "height": int(r["height"])
        })
    return rows

# -------------------- 요일 헤더 인식 강화 --------------------
def _day_headers(rgb: np.ndarray, x_edges: List[int], y_edges: List[int]) -> List[str]:
    """
    1) 상단 스트립(헤더)에서 토큰 OCR
    2) '월/화/...' 혹은 '월요일/...' 텍스트의 x-중심을 컬럼 중심에 매핑
    3) 부족하면 월~금/월~일 순서로 보정
    """
    H, W = rgb.shape[:2]
    top = 0
    bot = min(H-1, max(y_edges[1], int(H*0.15)))  # 헤더 영역
    strip = rgb[top:bot, :, :]
    tokens = _ocr_data(strip, psm=6, lang="kor")

    # 컬럼 중심
    centers = []
    for j in range(1, len(x_edges)-1):
        centers.append((x_edges[j] + x_edges[j+1]) // 2)
    days = [""] * len(centers)

    # 토큰 중 요일만 추출
    weekday_hits = []
    for t in tokens:
        tx = t["left"] + t["width"] // 2
        s = t["text"]
        # normalize '월요일' -> '월'
        hit = None
        for d in FULL_WEEKDAYS_KO:
            if d in s:
                hit = d[0]  # 첫 글자
                break
        if not hit:
            for d in WEEKDAYS_KO:
                if d in s:
                    hit = d
                    break
        if hit:
            weekday_hits.append((tx, hit))

    # 매핑: 가장 가까운 컬럼 중심에 요일 할당
    for tx, day in weekday_hits:
        idx = int(np.argmin([abs(tx - c) for c in centers])) if centers else None
        if idx is not None and 0 <= idx < len(days):
            days[idx] = day

    # 보정: 비어있으면 월~금(또는 월~일)로 채움
    if days.count("") > 0:
        if len(days) == 5:
            days = WEEKDAYS_KO[:5]
        elif len(days) == 6:
            days = WEEKDAYS_KO[:6]
        elif len(days) >= 7:
            days = WEEKDAYS_KO[:len(days)]
    return days

# -------------------- 강의 블록 탐지 --------------------
def _colored_mask(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    s = hsv[:, :, 1]
    mask_hsv = (s > 12).astype(np.uint8) * 255
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    a = lab[:, :, 1].astype(np.int16) - 128
    b = lab[:, :, 2].astype(np.int16) - 128
    chroma = np.sqrt(a*a + b*b)
    mask_lab = (chroma > 6).astype(np.uint8) * 255
    return cv2.max(mask_hsv, mask_lab)

def _text_mask(rgb: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.GaussianBlur(g, (3,3), 0)
    th = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 31, 10)
    return th

def _lecture_mask(rgb: np.ndarray) -> np.ndarray:
    # 컬러 + 텍스트 마스크를 OR
    mc = _colored_mask(rgb)
    mt = _text_mask(rgb)
    m = cv2.max(mc, mt)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3,3)), 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9,3)), 1)
    return m

# -------------------- 과목명 선택 로직 강화 --------------------
def _pick_subject_by_tokens(tokens: List[dict]) -> str:
    """
    - 한글 비중 높고
    - 강의실/이름(2~4자) 제외
    - 폰트가 큰(=height 큰) 토큰 우선
    """
    cand = []
    for t in tokens:
        s = t["text"].strip()
        if not s: continue
        s_nospace = re.sub(r"\s+", "", s)
        if ROOM_RE.search(s_nospace):  # 강의실 제거
            continue
        if NAME_RE.fullmatch(s_nospace):  # 사람 이름 제거
            continue
        if len(ONLY_KO.findall(s_nospace)) == 0:  # 한글 없음
            continue
        score = (t["height"], len(s_nospace), len(ONLY_KO.findall(s_nospace)))
        cand.append((score, s))

    if not cand:
        return ""

    # height/길이/한글비중 기준으로 정렬
    cand.sort(key=lambda z: (z[0][0], z[0][1], z[0][2]), reverse=True)
    subj = cand[0][1]
    # 괄호 속 옵션 제거: '과목명(캡스톤디자인)' -> '과목명'
    subj = re.sub(r'[\(\[][^\)\]]*[\)\]]', '', subj)
    subj = re.sub(r"\s+", "", subj)
    return subj

def _minutes_to_hhmm(m: int) -> str:
    m = int(round(m))
    h = (m // 60) % 24
    t = m % 60
    return f"{h:02d}:{t:02d}"

def _map_y_to_minutes(y: float, y0: int, hour_h: float, base_hour: int = 9) -> float:
    return base_hour * 60 + ((y - y0) / max(1e-6, hour_h)) * 60.0

def _snap(v: float, grid: int = 30) -> int:
    return int(round(v / grid) * grid)

# -------------------- 메인 파서 --------------------
def parse_single_image(rgb: np.ndarray) -> List[Dict]:
    H, W = rgb.shape[:2]
    binary = _binarize(rgb)
    y_lines, x_lines = _detect_grid(binary)

    # 엣지(셀 경계)
    y_edges = _edges_from_lines(y_lines, H)
    x_edges = _edges_from_lines(x_lines, W)
    if len(y_edges) < 3 or len(x_edges) < 3:
        # 그리드가 약하면 대충 헤더/본문 분할
        y_edges = [0, int(H * 0.15), H]
        x_edges = [0, int(W * 0.2), W]

    # 좌측 시간열/헤더 높이
    time_right = x_edges[1]
    header_bot = y_edges[1]

    # 요일 헤더 보강 인식
    days = _day_headers(rgb, x_edges, y_edges)
    num_day_cols = max(0, len(x_edges) - 2)
    if not days or len(days) != num_day_cols:
        # 컬럼 수에 맞춰 보정
        if num_day_cols <= 0:
            return []
        if num_day_cols <= 5:
            days = WEEKDAYS_KO[:num_day_cols]
        else:
            days = WEEKDAYS_KO[:num_day_cols]

    # 행 높이 → 시간 매핑 (09:00 기준)
    gaps = [y_edges[i+1] - y_edges[i] for i in range(1, len(y_edges)-2)] or [80]
    hour_h = float(np.median(gaps))
    y0 = y_edges[1]  # 09:00 근사 line (헤더 하단)
    base_hour = 9

    # 강의 블록 후보 (컬러 + 텍스트)
    mask = _lecture_mask(rgb[header_bot:y_edges[-1], time_right:W])
    Hc, Wc = mask.shape[:2]
    num, labels, stats, _ = cv2.connectedComponentsWithStats((mask>0).astype(np.uint8), connectivity=8)

    boxes = []
    area_min = int(H*W*0.0008)
    for i in range(1, num):
        x, y, w, h, a = stats[i]
        if a < area_min: 
            continue
        # 너무 가로로 넓거나 세로로 얇으면 제외
        if w < 20 or h < 20:
            continue
        # 원본 좌표로 변환
        boxes.append((x + time_right, y + header_bot, x + w + time_right, y + h + header_bot))

    # 컬럼 중심 (요일 매핑 용)
    col_centers = []
    for j in range(1, len(x_edges)-1):
        col_centers.append((x_edges[j] + x_edges[j+1]) // 2)

    entries: List[Dict] = []
    for (x1, y1, x2, y2) in boxes:
        # 어떤 요일 컬럼인지 (가까운 중심)
        col_idx = int(np.argmin([abs(((x1+x2)//2) - c) for c in col_centers])) if col_centers else None
        if col_idx is None or col_idx >= len(days):
            day_ko = ""
        else:
            day_ko = days[col_idx]

        # 시간 추정(+ 30분 스냅, 최소 60분 확보)
        s_min = _map_y_to_minutes(y1, y0, hour_h, base_hour)
        e_min = _map_y_to_minutes(y2, y0, hour_h, base_hour)
        s_min, e_min = _snap(s_min, 30), _snap(e_min, 30)
        if e_min - s_min < 60:
            e_min = s_min + 60

        # ROI OCR
        pad = 4
        y1p, y2p = max(0, y1+pad), min(H-1, y2-pad)
        x1p, x2p = max(0, x1+pad), min(W-1, x2-pad)
        if y2p <= y1p or x2p <= x1p:
            continue
        crop = rgb[y1p:y2p, x1p:x2p]
        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        # 이진화 두 가지 시도
        bin1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        bin2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, 31, 10)

        # 토큰 기반 주과목 선택 (height 큰 토큰 우선)
        toks = _ocr_data(bin1, psm=6, lang="kor+eng") + _ocr_data(bin2, psm=6, lang="kor+eng")
        subj = _pick_subject_by_tokens(toks)

        if not subj:
            # 라인 OCR 보조
            lines = [t.strip() for t in _ocr(bin1, psm=6).splitlines() if t.strip()]
            lines += [t.strip() for t in _ocr(bin2, psm=7).splitlines() if t.strip()]
            lines = list(dict.fromkeys(lines))
            cleaned = []
            for s in lines:
                s0 = re.sub(r"\s+", "", s)
                s0 = ROOM_RE.sub("", s0)
                if NAME_RE.fullmatch(s0):
                    continue
                if len(ONLY_KO.findall(s0)) == 0:
                    continue
                cleaned.append(s0)
            if cleaned:
                subj = re.sub(r'[\(\[][^\)\]]*[\)\]]', '', cleaned[0])

        entries.append({
            "subject": (subj or "미확인과목").strip() or "미확인과목",
            "weekday_ko": day_ko or "",
            "start": _minutes_to_hhmm(s_min),
            "end": _minutes_to_hhmm(e_min),
        })

    # 정렬: 요일→시작시각 (빈 요일은 뒤로)
    day_order = {d:i for i,d in enumerate(WEEKDAYS_KO)}
    entries.sort(key=lambda e: (day_order.get(e["weekday_ko"], 99), e["start"]))
    return entries

def parse_timetable_file_to_entries(path: str | Path) -> List[Dict]:
    p = Path(path)
    imgs: List[Image.Image] = []
    if p.suffix.lower() == ".pdf":
        imgs = _pdf_to_images(p)
    else:
        imgs = [_imread(p)]
    all_entries: List[Dict] = []
    for pil in imgs:
        rgb = np.array(pil.convert("RGB"))
        all_entries.extend(parse_single_image(rgb))
    # 과목명이 비어있는 것 정리
    for e in all_entries:
        e["subject"] = (e.get("subject") or "").strip() or "미확인과목"
    return all_entries
