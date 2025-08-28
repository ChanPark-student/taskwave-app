# app/services/timetable.py  (오프셋 학습형 안정판)

from __future__ import annotations
import os, re, logging, math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from collections import Counter, defaultdict

import cv2
import numpy as np
import pytesseract
import fitz
from PIL import Image
from pytesseract import Output
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================ 
# 런타임 설정(가독성과 안정성 위해 상수화)
# ============================================================ 
ENABLE_NEIGHBOR_FILTER: bool = False     # 사용 안함(불안정 소지)
FILL_THR: float = 0.006                  # 칸 배경 채움 임계(파스텔 대응)
VOCAB_SIM_THRESHOLD: float = 0.62        # 과목 어휘 사전 유사도 임계
ENABLE_DEDUPE: bool = False              # 블록 단위 모두 내보내기 위해 기본 False
MAX_DAYS: int = 7
FORCE_UNIFORM_EXPAND_TO_5: bool = True   # 월~금 기본 양식 보정 ON

# 병합 끄기(요청: 블록 단위 원본 유지)
DISABLE_FINAL_MERGE: bool = True

# 요일별 시간 스냅 기본 간격(분)
TIME_RANGE_MIN = 8 * 60   # 08:00
TIME_RANGE_MAX = 20 * 60  # 20:00
DAY_STEP_MINUTES: Dict[str, int] = {
    "월": 60, "화": 90, "수": 60, "목": 90, "금": 60, "토": 60, "일": 60
}
# 오프셋 후보(분) — 화/목의 10:30 등 대응 위해 0~55분 5분 간격 검색
# 스냅 허용오차(분)
SNAP_TOL_PRIMARY = 12.0
SNAP_TOL_RELAXED = 22.0

BASE_START_HOUR = 9  # 시간표 첫 줄 기준(09:00)

# 마스크/연결요소 파라미터(세로 합쳐짐 방지를 위해 수평 close만 적용)
COLOR_S_SAT = 12
COLOR_LAB_CHROMA = 6
AREA_MIN_FRACTION = 0.0008   # 전체 이미지 대비 최소 컴포넌트 면적
H_CLOSE_K = 9                # 수평 Close 커널 가로
H_CLOSE_ITERS = 1
OPEN_K = 3                   # Open 커널 크기(작은 노이즈 제거)

ALLOWED_IMAGE_SUFFIX = {'.png', '.jpg', '.jpeg', '.webp'}
KOR_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

# ── 시간 라벨 ────────────────────────────────────────────────
TIME_RE = re.compile(r"(오\s*전|오\s*후)?\s*([0-9]{1,2})\s*시")
TIME_RE_CONTAINS = re.compile(r"(?:오\s*전|오\s*후)?\s*[0-9]{1,2}\s*시")

# ── 이름/강의실 ─────────────────────────────────────────────
NAME_RE = re.compile(r'''
    ^            # 시작
    [가-힣]{2,4} # 한글 2~4자
    $            # 끝
''', re.X) 


ROOM_RE = re.compile(
    r"(?:[가-힣A-Za-z]{1,4}\s?\d{1,3}[A-Za-z]?\s*[-–]?\s?\d{2,4}\b)"
    r"|(?:\d{2,3}\s*[-–]\s*\d{2,4}\b)"
    r"|(?:[A-Za-z]{1,3}\d{2,4}\b)",
    flags=re.IGNORECASE
)
HANGUL_RUN_RE = re.compile(r'(?:(?<=^)|(?<=\s))((?:[가-힣]\s+)+[가-힣])(?=(?:\s|$))')
HANGUL_CH_RE = re.compile(r'''
    ^[가-힣]+$   # 한글만 1자 이상
''', re.X)
# ---- Tesseract 경로 주입 ----
_candidates = [
    settings.TESSERACT_CMD,
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
]
tess_path = next((p for p in _candidates if p and os.path.isfile(p)), None)
if not tess_path:
    raise RuntimeError("Tesseract 실행 파일을 찾지 못했습니다. .env 의 TESSERACT_CMD를 점검하세요.")
pytesseract.pytesseract.tesseract_cmd = tess_path
if getattr(settings, "TESSDATA_PREFIX", None):
    os.environ["TESSDATA_PREFIX"] = settings.TESSDATA_PREFIX


# ---------- 데이터 클래스 ----------
@dataclass
class ParsedSlot:
    weekday: str
    start_time: str    # "HH:MM"
    end_time: Optional[str] = None
    title: str = ""
    professor: Optional[str] = None
    location: Optional[str] = None
    raw_text: str = ""


# ---------- 과목 사전 ----------
from difflib import SequenceMatcher
DEFAULT_COURSE_VOCAB = {
    "재무경영분석",
    "품질공학",
    "산업공학SW활용",
    "휴먼인터페이스공학",
    "데이터분석과응용",
}
COURSE_VOCAB = set(getattr(settings, "COURSE_VOCAB", [])) or DEFAULT_COURSE_VOCAB


# ---------- 유틸 ----------

def _prune_tiny_day_columns(x_edges: List[int], W: int, min_frac: float = 0.07) -> List[int]:
    if len(x_edges) < 4:
        return x_edges
    kept = [x_edges[0], x_edges[1]]
    for i in range(2, len(x_edges)-1):
        w = x_edges[i+1] - x_edges[i]
        if w >= int(W * min_frac):
            kept.append(x_edges[i])
    kept.append(x_edges[-1])
    kept = sorted(set(kept))
    return kept

def _weekday_for_column(c: int, days: List[str]) -> str:
    idx = c - 1
    if 0 <= idx < len(days) and days[idx]:
        return days[idx]
    if days:
        return days[min(idx, len(days)-1)]
    return KOR_WEEKDAYS[idx % 7]


def _vocab_correct(s: str, vocab: set[str]) -> Optional[str]:
    if not s:
        return None
    base = re.sub(r'\s+', '', s)
    best, best_r = None, 0.0
    for v in vocab:
        r = SequenceMatcher(None, base, re.sub(r'\s+', '', v)).ratio()
        if r > best_r:
            best_r, best = r, v
    return best if best_r >= VOCAB_SIM_THRESHOLD else None


import re

def _normalize_line(s: str) -> str:
    s = " ".join(s.split())
    s = HANGUL_RUN_RE.sub(lambda m: m.group(0).replace(' ', ''), s)
    s = re.sub(r'(\d)\s*[-–]\s*(\d)', r'\1-\2', s)
    # 앞/뒤의 따옴표류 제거: ", “, ”, ', `
    s = re.sub(r"^[\"“”'`]+|[\"“”'`]+$", "", s)
    s = re.sub(r'\b(?:5|S)\s*/\s*', 'SW', s)  # '산업공학 5/ 활용' → '산업공학SW활용'
    return s



def _add_hours_str(t: Optional[str], dh: int) -> Optional[str]:
    if not t:
        return None
    try:
        h = int(t[:2]); m = int(t[3:5])
    except Exception:
        return None
    h = (h + dh) % 24
    return f"{h:02d}:{m:02d}"


def _ocr_string(img, psm: int, lang="kor+eng") -> str:
    cfg = f"--psm {psm} --oem 1 -c preserve_interword_spaces=1"
    return pytesseract.image_to_string(img, lang=lang, config=cfg)

def _binarize(rgb: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    return thr

def _build_edges_from_centers(centers: List[int], whole: int) -> List[int]:
    centers = [int(c) for c in list(centers or []) if c is not None and not (isinstance(c, float) and np.isnan(c))]
    centers = sorted(centers)
    if not centers:
        return [0, whole]
    edges = [0]
    for a, b in zip(centers, centers[1:]):
        try:
            edges.append((int(a) + int(b)) // 2)
        except Exception:
            continue
    edges.append(whole)
    edges = sorted(set(int(e) for e in edges if e is not None))
    return edges

def _group_positions(pos: np.ndarray, gap: int) -> List[int]:
    if pos is None or len(pos) == 0:
        return []
    pos = [int(p) for p in list(pos) if p is not None and not (isinstance(p, float) and np.isnan(p))]
    if len(pos) == 0:
        return []
    pos = np.sort(np.array(pos, dtype=int))
    groups, cur = [], [pos[0]]
    for p in pos[1:]:
        if p - cur[-1] <= gap:
            cur.append(p)
        else:
            groups.append(int(np.median(cur)))
            cur = [p]
    groups.append(int(np.median(cur)))
    return groups

def _detect_grid_lines(binary: np.ndarray) -> Tuple[List[int], List[int]]:
    """
    수평/수직 격자선 y/x 좌표
    """
    h, w = binary.shape[:2]

    best = (0, [], [])
    for pol in (binary, cv2.bitwise_not(binary)):
        work = cv2.medianBlur(pol, 3)
        work = cv2.dilate(work, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=2)

        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, int(w * 0.025)), 1))
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(12, int(h * 0.025))))
        h_img = cv2.morphologyEx(work, cv2.MORPH_OPEN, h_kernel, iterations=1)
        v_img = cv2.morphologyEx(work, cv2.MORPH_OPEN, v_kernel, iterations=1)

        y_lines = _group_positions(np.where(h_img.sum(axis=1) > 255 * max(8, int(w * 0.02)))[0], gap=8)
        x_lines = _group_positions(np.where(v_img.sum(axis=0) > 255 * max(8, int(h * 0.02)))[0], gap=8)

        score = len(y_lines) + len(x_lines)
        if score > best[0]:
            best = (score, y_lines, x_lines)

    y_lines, x_lines = best[1], best[2]

    def _coarsen(pos: List[int], gap: int) -> List[int]:
        if not pos: return []
        pos = sorted(pos)
        out, cur = [], [pos[0]]
        for p in pos[1:]:
            if p - cur[-1] <= gap:
                cur.append(p)
            else:
                out.append(int(np.mean(cur)))
                cur = [p]
        out.append(int(np.mean(cur)))
        return out

    y_lines = _coarsen(y_lines, gap=24)
    x_lines = _coarsen(x_lines, gap=max(60, int(w * 0.06)))
    return y_lines, x_lines


# ---------- 텍스트기반 열/행 추론 ----------
def _infer_columns_from_words(df, W: int, H: int, header_h: int, time_w_guess: int) -> Tuple[List[int], int]:
    if df is None or len(df) == 0:
        return [0, time_w_guess, W], time_w_guess

    work = df.copy()
    work = work[work["top"] > header_h]
    cx = (work["left"] + work["width"] / 2).astype(int).to_numpy()
    if len(cx) < 20:
        return [0, time_w_guess, W], time_w_guess

    bin_w = max(30, W // 120)
    bins = np.arange(0, W + bin_w, bin_w)
    hist, edges = np.histogram(cx, bins=bins)
    thr = max(5, int(np.percentile(hist, 85)))
    peaks = np.where(hist >= thr)[0]
    centers = []
    for i in peaks:
        x_l = edges[i]; x_r = edges[i+1]
        mask = (cx >= x_l) & (cx < x_r)
        if mask.sum() < 5: continue
        centers.append(int(np.median(cx[mask])))

    centers = sorted(set(centers))
    if len(centers) < 4:
        return [0, time_w_guess, W], time_w_guess

    work["cx"] = (work["left"] + work["width"]/2).astype(int)
    time_idx = 0
    best_score, best_i = -1e9, 0
    for i, c in enumerate(centers[: min(3, len(centers))]):
        mask = (work["cx"] >= c - bin_w) & (work["cx"] < c + bin_w)
        seg = work[mask]
        if len(seg) == 0: continue
        txt = seg["text"].astype(str)
        score = 0.0
        score += 3.0 * float(txt.str.contains(TIME_RE_CONTAINS, regex=True, na=False).mean())
        dig_ratio = txt.apply(lambda s: sum(ch.isdigit() for ch in s) / max(1, len(s))).mean()
        score += 1.5 * float(dig_ratio)
        score += 0.2 * (1.0 - (c / max(1.0, W)))
        if score > best_score:
            best_score, best_i = score, i
    time_idx = best_i

    time_center = centers[time_idx]
    day_centers = [c for i, c in enumerate(centers) if i != time_idx]
    day_centers = sorted(day_centers)
    if len(day_centers) < 4:
        return [0, time_w_guess, W], time_w_guess

    all_centers = [time_center] + day_centers
    all_centers.sort()
    edges = [0]
    for a, b in zip(all_centers, all_centers[1:]):
        edges.append((a + b) // 2)
    edges.append(W)

    tc = time_center
    dc = min(day_centers) if day_centers else int(W*0.35)
    time_w = int((tc + dc) / 2)
    time_w = max(int(W*0.10), min(time_w, int(W*0.35)))

    if edges[1] != time_w:
        edges[1] = time_w
        edges = sorted(set(e for e in edges if 0 <= e <= W))
        if edges[0] != 0: edges = [0] + edges
        if edges[-1] != W: edges = edges + [W]
    return edges, time_w

def _infer_rows_from_words(df, H: int, header_h: int, footer_h: int = 0) -> List[int]:
    if df is None or len(df) == 0:
        return [0, int(H*0.12), H]
    work = df.copy()
    work = work[(work["top"] > header_h) & (work["top"] < (H - footer_h - 1))]
    if len(work) < 20:
        return [0, int(H*0.12), H]
    cy = (work["top"] + work["height"]/2).astype(int).to_numpy()

    bin_h = max(14, H // 120)
    bins = np.arange(0, H + bin_h, bin_h)
    hist, edges = np.histogram(cy, bins=bins)
    thr = max(5, int(np.percentile(hist, 80)))
    peaks = np.where(hist >= thr)[0]

    centers = []
    for i in peaks:
        y_t = edges[i]; y_b = edges[i+1]
        mask = (cy >= y_t) & (cy < y_b)
        if mask.sum() < 5: continue
        centers.append(int(np.median(cy[mask])))

    centers = sorted(set(centers))
    if len(centers) < 4:
        return [0, int(H*0.12), H]

    y_edges = [0]
    for a, b in zip(centers, centers[1:]):
        y_edges.append((a + b) // 2)
    y_edges.append(H)

    if y_edges[1] - header_h > max(24, int(H*0.06)):
        y_edges[1] = header_h + max(12, int(H*0.03))
    return y_edges

def _row_times_from_left_ocr(df, H: int, time_w: int) -> Tuple[List[str], List[int], List[int]]:
    left = df[df.left < time_w].copy()
    keys = ["page_num", "block_num", "par_num", "line_num"]
    g = (left.groupby(keys, as_index=False)
           .agg(text=("text", lambda s: " ".join(s)),
                top=("top", "min"), height=("height", "max")))
    g["top"] = pd.to_numeric(g["top"], errors="coerce").fillna(0)
    g["height"] = pd.to_numeric(g["height"], errors="coerce").fillna(0)
    g["cy"] = (g["top"] + g["height"] / 2.0)
    row_labels  = g["text"].tolist()
    row_centers = [int(v) for v in g["cy"].tolist() if pd.notna(v)]

    row_edges   = _build_edges_from_centers(row_centers, H)

    def _to_24h(s: str) -> Optional[str]:
        m = TIME_RE.search(s or "")
        if not m:
            return None
        per, hh = m.groups()
        h = int(hh)
        if per and "후" in per and h < 12: h += 12
        if per and "전" in per and h == 12: h = 0
        return f"{h:02d}:00"

    row_starts = [_to_24h(s) for s in row_labels]
    if not any(row_starts):
        return [], row_centers, row_edges

    idxs = [i for i, t in enumerate(row_starts) if t]
    if not idxs:
        return [], row_centers, row_edges
    first = idxs[0]

    hrs = [None]*len(row_starts)
    base = int(row_starts[first][:2]); hrs[first] = base
    h = base
    for i in range(first-1, -1, -1):
        h = (h - 1) % 24; hrs[i] = h
    h = base
    for i in range(first+1, len(row_starts)):
        h = (h + 1) % 24; hrs[i] = h
    row_starts = [f"{h:02d}:00" for h in hrs]
    return row_starts, row_centers, row_edges


def _cell_has_text(df, x1: int, y1: int, x2: int, y2: int, min_chars: int = 4) -> bool:
    if df is None or len(df) == 0:
        return False
    w = max(1, x2 - x1)
    shrink = int(w * 0.06)
    sx1, sx2 = x1 + shrink, x2 - shrink
    if sx2 <= sx1:
        sx1, sx2 = x1, x2

    cx = df["left"] + df["width"] / 2
    cy = df["top"]  + df["height"] / 2
    mask = (cx >= sx1) & (cx < sx2) & (cy >= y1) & (cy < y2)
    if not mask.any():
        return False

    sel = df.loc[mask, "text"].astype(str)
    total_chars = int(sel.str.len().sum())
    ko_chars    = int(sel.str.count(r'[가-힣]').sum())
    return (ko_chars >= 2) or (total_chars >= max(min_chars, 8) and ko_chars >= 2)


def _cell_fill_ratio(rgb: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> float:
    roi = rgb[max(0, y1):max(y1+1, y2), max(0, x1):max(x1+1, x2)]
    if roi.size == 0:
        return 0.0
    try:
        H, W = roi.shape[:2]
        hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        s = hsv[:, :, 1]
        mask_hsv = (s > COLOR_S_SAT)

        lab = cv2.cvtColor(roi, cv2.COLOR_RGB2LAB)
        a = lab[:, :, 1].astype(np.int16) - 128
        b = lab[:, :, 2].astype(np.int16) - 128
        chroma = np.sqrt(a*a + b*b)
        mask_lab = (chroma > COLOR_LAB_CHROMA)

        mask = np.logical_or(mask_hsv, mask_lab).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                                cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)),
                                iterations=1)
        filled = int((mask > 0).sum())
        return float(filled) / float(H * W)
    except Exception:
        return 0.0


# ---------- 열/요일 확정 ----------
def _days_from_header_ocr(rgb: np.ndarray, x_edges: List[int], y_edges: List[int]) -> List[str]:
    if len(y_edges) < 2:
        return []
    top, bot = y_edges[0] + 2, y_edges[1] - 2
    days = []
    for j in range(1, len(x_edges) - 1):
        l, r = x_edges[j] + 3, x_edges[j + 1] - 3
        crop = rgb[top:bot, l:r]
        txt = _ocr_string(crop, psm=7)
        day = next((d for d in KOR_WEEKDAYS if d in txt), "")
        days.append(day)
    if days and (days.count("") >= 1) and (5 <= len(days) <= 7):
        for i, d in enumerate(KOR_WEEKDAYS[:len(days)]):
            if not days[i]:
                days[i] = d
    return days

def _infer_columns_from_header_days(df, W: int, header_h: int, time_w_guess: int) -> Tuple[List[int], int, List[int]]:
    if df is None or len(df) == 0:
        return [0, time_w_guess, W], time_w_guess, []

    dfh = df[(df["top"] >= 0) & (df["top"] < int(header_h * 1.4))].copy()
    if len(dfh) == 0:
        return [0, time_w_guess, W], time_w_guess, []

    pat = "|".join(KOR_WEEKDAYS)
    hits = dfh[dfh["text"].astype(str).str.contains(pat, regex=True, na=False)]
    if len(hits) < 4:
        return [0, time_w_guess, W], time_w_guess, []

    centers = []
    for _, r in hits.iterrows():
        t = str(r["text"])
        if any(d in t for d in KOR_WEEKDAYS):
            cx = int(r["left"] + r["width"] / 2)
            centers.append(cx)
    if len(centers) < 4:
        return [0, time_w_guess, W], time_w_guess, []

    centers = _group_positions(np.array(centers), gap=max(20, int(W * 0.02)))
    centers = sorted(set(int(c) for c in centers))
    if len(centers) < 4:
        return [0, time_w_guess, W], time_w_guess, []

    x_edges = [0, time_w_guess]
    for a, b in zip(centers, centers[1:]):
        x_edges.append((a + b) // 2)
    x_edges.append(W)
    x_edges = sorted(set(int(e) for e in x_edges))

    if len(x_edges) >= 3 and x_edges[1] >= x_edges[2]:
        x_edges[1] = max(int(W * 0.10), min(int(W * 0.35), x_edges[2] - 10))

    return x_edges, x_edges[1], centers

def _resolve_columns(df, rgb, W, H, header_h, x_lines, time_w_guess, debug_lines) -> Tuple[List[int], List[str], int]:
    def _uniform5_from(x_edges_now: List[int]) -> List[int]:
        left  = x_edges_now[1]
        right = x_edges_now[-1]
        k = 5
        step = max(1, (right - left) // k)
        mids = [left + step * i for i in range(1, k)]
        return sorted(set([0, left] + mids + [right]))

    x_edges = [0, int(time_w_guess), W]
    time_w  = int(time_w_guess)
    strategy = "fallback"

    if len(x_lines) >= 4:
        edges_grid = [0] + [(x_lines[i] + x_lines[i+1]) // 2 for i in range(len(x_lines)-1)] + [W]
        edges_grid = _prune_tiny_day_columns(edges_grid, W, min_frac=0.07)
        x_edges, time_w = edges_grid, edges_grid[1]
        strategy = "grid"

        xh, tw, _day_centers = _infer_columns_from_header_days(df, W, header_h, time_w)
        if len(xh) >= 6 and (len(xh) - 2) > (len(edges_grid) - 2):
            x_edges, time_w = xh, tw
            strategy = "header-days>grid"
    else:
        xh, tw, _day_centers = _infer_columns_from_header_days(df, W, header_h, time_w_guess)
        if len(xh) >= 6:
            x_edges, time_w = xh, tw
            strategy = "header-days"
        else:
            xw, tww = _infer_columns_from_words(df, W, H, header_h, time_w_guess)
            if len(xw) >= 6:
                x_edges, time_w = xw, tww
                strategy = "word-hist"

    num_day_cols = max(0, len(x_edges) - 2)
    if FORCE_UNIFORM_EXPAND_TO_5 and num_day_cols < 5 and len(x_edges) >= 3:
        x_edges = _uniform5_from(x_edges)
        time_w  = x_edges[1]
        strategy += " + uniform5"

    debug_lines.append(f"[COL] strategy={strategy} -> edges={x_edges} (C={len(x_edges)-1})")

    y_edges_tmp = [0, max(2, int(H * 0.18)), H]
    days = _days_from_header_ocr(rgb, x_edges, y_edges_tmp)
    num_day_cols = max(0, len(x_edges) - 2)
    if not days or len(days) != num_day_cols or any(d not in KOR_WEEKDAYS for d in days):
        days = KOR_WEEKDAYS[:min(MAX_DAYS, num_day_cols)]

    return x_edges, days, time_w


# ---------- 행/시각 확정 ----------
def _resolve_rows(df, H, header_h, y_lines, time_w, debug_lines) -> Tuple[List[int], List[str]]:
    if len(y_lines) >= 6:
        y_edges = [0] + [(y_lines[i] + y_lines[i+1]) // 2 for i in range(len(y_lines)-1)] + [H]
        debug_lines.append(f"[ROW] grid-based edges({len(y_edges)})")
    else:
        row_starts_raw, row_centers, _ = _row_times_from_left_ocr(df, H, time_w=time_w)
        debug_lines.append(f"[ROW] raw centers={row_centers[:10]}")
        debug_lines.append(f"[ROW] raw starts={row_starts_raw}")

        if len(row_centers) >= 2:
            y_edges = _build_edges_from_centers(row_centers, H)
            debug_lines.append(f"[ROW] centers→edges({len(y_edges)})")
        else:
            y_edges = _infer_rows_from_words(df, H, header_h)
            debug_lines.append(f"[ROW] infer-words edges({len(y_edges)})")

    R = max(1, len(y_edges) - 1)
    row_starts, row_centers2, _ = _row_times_from_left_ocr(df, H, time_w=time_w)

    def _align_row_starts_to_bands(y_edges, row_centers, row_starts):
        num_rows = max(0, len(y_edges) - 2)
        if num_rows <= 0:
            return []
        def band_of(y):
            for i in range(len(y_edges)-1):
                if y_edges[i] <= y < y_edges[i+1]:
                    return i
            return 1
        anchors = []
        for cy, t in zip(row_centers, row_starts or []):
            if not t: continue
            b = max(0, min(num_rows-1, band_of(int(cy)) - 1))
            try:
                h = int(t[:2])
            except Exception:
                continue
            anchors.append((b, h))

        if anchors:
            anchors.sort(key=lambda x: x[0])
            b0, h0 = anchors[0]
            base = (h0 - b0) % 24
        else:
            base = BASE_START_HOUR

        out = [f"{(base + i) % 24:02d}:00" for i in range(num_rows)]
        return out

    final_row_starts = _align_row_starts_to_bands(y_edges, row_centers2, row_starts)
    num_rows = max(0, len(y_edges) - 2)
    if (not final_row_starts) or (len(final_row_starts) != num_rows) or (final_row_starts[0] >= "12:00"):
        base = BASE_START_HOUR
        final_row_starts = [f"{(base + i) % 24:02d}:00" for i in range(num_rows)]
        debug_lines.append("[ROW] fallback to 09:00-based sequence")

    debug_lines.append(f"[ROW] aligned starts={final_row_starts}")
    return y_edges, final_row_starts


# ---------- 텍스트 재구성/세로뭉침 ----------
def _fuse_vertical_hangul(words: List[dict]) -> List[str]:
    if not words:
        return []
    chars = []
    for w in words:
        t = str(w.get("text", "")).strip()
        if len(t) == 1 and HANGUL_CH_RE.match(t):
            chars.append({
                "ch": t,
                "x": int(w["left"] + w["width"] / 2),
                "y": int(w["top"]  + w["height"]/ 2),
                "h": int(w["height"]),
                "w": int(w["width"]),
            })
    if len(chars) < 3:
        return []
    chars.sort(key=lambda c: c["x"])
    avg_w = max(1, int(np.median([c["w"] for c in chars])))
    x_tol = max(6, int(avg_w * 0.8))

    columns = [[chars[0]]]
    for c in chars[1:]:
        if abs(c["x"] - columns[-1][-1]["x"]) <= x_tol:
            columns[-1].append(c)
        else:
            columns.append([c])

    fused = []
    for col in columns:
        col.sort(key=lambda c: c["y"])
        s = "".join(c["ch"] for c in col)
        if len(s) >= 3:
            fused.append("[V]" + s)
    return fused


def _reconstruct_lines_by_yx(words: List[dict]) -> List[str]:
    if not words:
        return []
    words = sorted(words, key=lambda w: (w["top"], w["left"]));
    lines, cur = [], []
    avg_h = max(1, int(np.mean([w["height"] for w in words])))
    y_tol = int(0.6 * avg_h)
    for w in words:
        if not cur or abs(w["top"] - cur[-1]["top"]) <= y_tol:
            cur.append(w)
        else:
            lines.append(sorted(cur, key=lambda x: x["left"]))
            cur = [w]
    if cur:
        lines.append(sorted(cur, key=lambda x: x["left"]))
    out = []
    for ln in lines:
        s = " ".join(w["text"] for w in ln if w["text"])
        if s:
            out.append(s)
    return out


SURNAMES = set(list("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우민유제기"))
def _looks_korean_name(s: str) -> bool:
    return bool(NAME_RE.fullmatch(s)) and s[0] in SURNAMES


def _split_prof_loc(line: str) -> tuple[Optional[str], Optional[str]]:
    prof, loc = None, None
    s = re.sub(r'^\ \[V\]', '', line.strip())
    m_join = re.search(r'([가-힣]{2,4})\s*((?:공|[A-Za-z])\s?\d{1,3}[A-Za-z]?\s*[-–]?\s?\d{2,4})', s)
    if m_join:
        cand_prof = m_join.group(1)
        cand_loc  = re.sub(r'\s+', '', m_join.group(2))
        if _looks_korean_name(cand_prof): prof = cand_prof
        loc = cand_loc

    if loc is None:
        m = ROOM_RE.search(s)
    if m:
        loc = m.group(0).replace(' ', '')
        head = s[:m.start()].strip()
        # head의 끝에서 한글 이름(2~4자) 캡처
        mn = re.search(r'([가-힣]{2,4})\s*$', head)
        if mn and _looks_korean_name(mn.group(1)):
            prof = prof or mn.group(1)


    if prof is None and not any(ch.isdigit() for ch in s):
        mn = re.match(r'^([가-힣]{2,4})\b', s)
        if mn and _looks_korean_name(mn.group(1)):
            prof = mn.group(1)

    if loc:
        mloc = ROOM_RE.search(loc)
        if mloc:
            loc = mloc.group(0)
    return prof, loc


COURSE_SUFFIXES = ("공학", "학", "론", "설계", "실습", "응용", "분석", "디자인", "캡스톤디자인", "활용")

def _score_title(s: str, freq: int, idx: int, prof_hint: Optional[str]) -> float:
    L  = len(s)
    ko = len(re.findall(r'[가-힣]', s))
    en = len(re.findall(r'[A-Za-z]', s))
    dig = sum(ch.isdigit() for ch in s)
    hy  = s.count('-') + s.count('–') + s.count('/')
    looks_room = bool(ROOM_RE.search(s))
    is_name    = bool(NAME_RE.fullmatch(s))
    letters    = ko + en + dig
    ko_ratio   = ko / max(1, letters)
    ascii_ratio= (en + dig) / max(1, letters)
    suf_bonus  = 1.6 if (any(s.endswith(sf) for sf in COURSE_SUFFIXES) and L >= 3) else 0.0

    prof_pen = 0.0
    if prof_hint:
        if prof_hint in s: prof_pen -= 2.0
        tail2 = prof_hint[-2:] if len(prof_hint) >= 2 else ""
        if tail2 and tail2 in s: prof_pen -= 1.0

    return (
        1.3 * ko_ratio * L
        + 0.4 * min(freq, 5)
        + suf_bonus
        - 1.6 * ascii_ratio
        - 1.0 * hy
        - 2.5 * looks_room
        - 2.0 * is_name
        - 0.2 * idx
        + prof_pen
    )

def _choose_fields_from_lines(lines: List[str], line_freq: Counter) -> Tuple[str, Optional[str], Optional[str], str]:
    if not lines:
        return "", None, None, ""

    parsed = []
    for raw in lines[:8]:
        is_v = raw.startswith("[V]")
        clean = re.sub(r'^\ \[V\]', '', raw)
        parsed.append((raw, clean, is_v))

    loc_cands  = []
    prof_cands = []

    def _score_prof_local(name: str) -> float:
        ok_name = bool(NAME_RE.fullmatch(name))
        has_digit = any(ch.isdigit() for ch in name)
        surname_ok = (name and name[0] in SURNAMES)
        return (2.0 if ok_name else 0.0) + (1.0 if surname_ok else 0.0) - (1.0 if has_digit else 0.0)

    for idx, (_raw, s, is_v) in enumerate(parsed):
        p_cand, l_cand = _split_prof_loc(s)

        if l_cand:
            dig = sum(ch.isdigit() for ch in l_cand)
            ls  = 2.0 + 0.25 * dig + (0.8 if p_cand else 0.0) - 0.05*idx
            loc_cands.append((ls, l_cand, idx, p_cand))
        else:
            m = ROOM_RE.search(s)
            if m:
                l = m.group(0).replace(' ', '')
                dig = sum(ch.isdigit() for ch in l)
                ls  = 1.8 + 0.2 * dig - 0.05*idx
                loc_cands.append((ls, l, idx, None))

        if p_cand:
            ps  = _score_prof_local(p_cand) + (1.2 if l_cand else 0.0) - 0.05*idx
            if is_v and not l_cand:
                ps -= 2.2
            prof_cands.append((ps, p_cand, idx, bool(l_cand), is_v))

    best_loc, best_loc_idx, best_loc_prof = None, None, None
    if loc_cands:
        loc_cands.sort(key=lambda x: x[0], reverse=True)
        best_loc      = loc_cands[0][1]
        best_loc_idx  = loc_cands[0][2]
        best_loc_prof = loc_cands[0][3]

    best_prof, best_prof_is_v, best_prof_has_loc = None, False, False
    if best_loc_prof:
        best_prof = best_loc_prof
        best_prof_has_loc = True
    elif prof_cands:
        prof_cands.sort(key=lambda x: (x[3], x[0]), reverse=True)
        best_prof         = prof_cands[0][1]
        best_prof_has_loc = prof_cands[0][3]
        best_prof_is_v    = prof_cands[0][4]

    def _title_penalty_contains_prof(title: str, prof: Optional[str]) -> float:
        if not title or not prof:
            return 0.0
        pen = 0.0
        if prof in title: pen += 1.5
        tail2 = prof[-2:] if len(prof) >= 2 else ""
        if tail2 and tail2 in title: pen += 0.8
        return pen

    lex = [s for (_, s, _) in parsed if any(s.endswith(sf) for sf in COURSE_SUFFIXES)]
    lex = [s for s in lex if len(re.sub(r'[^가-힣]','', s)) >= 3]
    title_override = None
    if lex:
        lex.sort(key=lambda z: (len(re.sub(r'[^가-힣]','', z)),
                                -sum(ch.isdigit() or ('A' <= ch <= 'z') for ch in z)),
                 reverse=True)
        title_override = lex[0]

    best_title, best_ts = None, -1e9
    for idx, (_raw, s, _is_v) in enumerate(parsed[:6]):
        ts = _score_title(s, line_freq.get(s, 0), idx, best_prof)
        ts -= _title_penalty_contains_prof(s, best_prof)
        if ts > best_ts:
            best_ts, best_title = ts, s
    if title_override:
        best_title = title_override

    if best_title:
        if best_prof and best_prof in best_title:
            best_title = best_title.replace(best_prof, "").strip()
        best_title = ROOM_RE.sub("", best_title).strip()

    if best_title and NAME_RE.fullmatch(best_title):
        for (_raw, s, _is_v) in parsed:
            if not NAME_RE.fullmatch(s) and not ROOM_RE.search(s):
                if len(re.sub(r'[^가-힣]', '', s)) >= 3:
                    best_title = s.strip()
                    break

    vc = _vocab_correct(best_title, COURSE_VOCAB)
    if not vc:
        for (_raw, s, _is_v) in parsed:
            vc = _vocab_correct(s, COURSE_VOCAB)
            if vc:
                break
    if vc:
        best_title = vc

    def _is_valid_title_strict(title: str) -> bool:
        if not title: return False
        cleaned = re.sub(r'\s+', '', title)
        ko = len(re.findall(r'[가-힣]', cleaned))
        return (ko >= 2) or (_vocab_correct(cleaned, COURSE_VOCAB) is not None)
    if not _is_valid_title_strict(best_title):
        best_title = ""

    if best_prof and best_prof_is_v and not best_prof_has_loc:
        best_prof = None

    return best_title, best_prof, best_loc, "\n".join(s for (_raw, s, _is_v) in parsed)

def _merge_contiguous_slots(slots: List[ParsedSlot]) -> List[ParsedSlot]:
    key = lambda s: (s.weekday, s.title.strip(), s.professor or "", s.location or "")
    slots = sorted(slots, key=lambda s: (s.weekday, s.start_time, s.end_time or ""))
    merged: List[ParsedSlot] = []
    for s in slots:
        if merged and key(merged[-1]) == key(s) and merged[-1].end_time == s.start_time:
            merged[-1].end_time = s.end_time
            prev_raw = merged[-1].raw_text or ""
            curr_raw = s.raw_text or ""
            merged[-1].raw_text = (prev_raw + (("\n" + curr_raw) if curr_raw else "")).strip()
        else:
            merged.append(s)
    return merged


# ---------- 시간 스냅/매핑 유틸 ----------
def _hour_grid_model(y_edges: List[int]) -> Tuple[int, float]:
    """
    y_edges: [0, header_bottom, row1_bottom, ..., H]
    반환: (y_09_top_px, hour_height_px)
    """
    if len(y_edges) < 3:
        return 0, 80.0
    y0 = int(y_edges[1])  # 콘텐츠 시작(09:00) 라인
    gaps = [y_edges[i+1]-y_edges[i] for i in range(1, len(y_edges)-2)]
    hour_h = float(np.median(gaps)) if gaps else 80.0
    return y0, hour_h

def _refine_y0_with_left_labels(y0: int, hour_h: float, df, time_w: int, H: int) -> int:
    """
    왼쪽 시간 라벨(오전/오후 n시)의 y-중심과 실제 시각(HH:00)을 비교해
    y0를 미세 조정(분 단위 바이어스를 제거).
    """
    try:
        row_starts, row_centers, _ = _row_times_from_left_ocr(df, H, time_w)
        diffs = []
        for cy, t in zip(row_centers, row_starts or []):
            if not t:
                continue
            m_true = int(t[:2]) * 60  # HH:00 → 분
            m_hat = BASE_START_HOUR * 60 + ((float(cy) - float(y0)) / max(1e-6, float(hour_h))) * 60.0
            diffs.append(m_hat - m_true)
        if len(diffs) >= 2:
            bias_min = float(np.median(diffs))  # 분 단위 바이어스
            y0_adj = float(y0) + (bias_min / 60.0) * float(hour_h)
            return int(round(y0_adj))
    except Exception:
        pass
    return y0

def _y_to_minutes(y: float, y0: int, hour_h: float) -> float:
    return BASE_START_HOUR * 60 + ( (y - y0) / max(1e-6, hour_h) ) * 60.0

def _minutes_to_hhmm(m: int) -> str:
    m = int(round(m))
    h = (m // 60) % 24
    mi = m % 60
    return f"{h:02d}:{mi:02d}"

def _offset_candidates_for_step(step: int) -> list[int]:
    # 60분 격자: 항상 정시 시작
    if step == 60:
        return [0]
    # 90분 격자: 0 또는 30분 오프셋만 허용(대학 시간표 관행)
    if step == 90:
        return [0, 30]
    # 예외적인 시간표만 폭넓게
    return list(range(0, step, 5))

def _anchors_for_weekday(day: str, offset_min: int = 0) -> List[int]:
    """요일별 간격과 오프셋으로 [TIME_RANGE_MIN, TIME_RANGE_MAX] 앵커 생성"""
    step = DAY_STEP_MINUTES.get(day, 60)
    start = TIME_RANGE_MIN
    end   = TIME_RANGE_MAX
    # 첫 앵커는 offset_min 이상이면서 최소 start 이상이 되도록
    k0 = math.ceil((start - offset_min) / step) if step > 0 else 0
    first = offset_min + step * max(0, k0)
    anchors = []
    x = first
    while x <= end:
        anchors.append(int(x))
        x += step
    return anchors

def _snap_to_anchors(value_min: float, anchors: List[int], tol_min: float) -> Optional[int]:
    if not anchors:
        return None
    diffs = [abs(value_min - a) for a in anchors]
    j = int(np.argmin(diffs))
    if diffs[j] <= tol_min:
        return anchors[j]
    return None

def _round_by_step(value_min: float, step: int) -> int:
    """자정 기준 step 라운드(안전장치)"""
    if step <= 0:
        return int(round(value_min))
    return int(round(value_min / step)) * step

def _estimate_offset_for_day(samples: list[tuple[float, float]], step: int) -> tuple[int, float, float]:
    """
    주어진 (시작, 끝) 분 단위 샘플로 요일 오프셋 δ를 추정.
    반환: (best_offset, coverage_ratio, mean_abs_error_at_best)
    """
    if not samples or step <= 0:
        return 0, 0.0, 9999.0

    best_off, best_score, best_mae = 0, -1.0, 1e9
    for δ in _offset_candidates_for_step(step):
        # step, δ로 앵커 직접 생성
        anchors = []
        k0 = math.ceil((TIME_RANGE_MIN - δ) / step)
        a = δ + step * max(0, k0)
        while a <= TIME_RANGE_MAX:
            anchors.append(int(a))
            a += step

        ok = 0
        errs = []
        for s, e in samples:
            sn = _snap_to_anchors(s, anchors, SNAP_TOL_PRIMARY)
            en = _snap_to_anchors(e, anchors, SNAP_TOL_PRIMARY)
            if sn is not None and en is not None:
                ok += 1
                errs.append(abs(s - sn) + abs(e - en))
            else:
                if anchors:
                    errs.append(min(abs(s - a0) for a0 in anchors) +
                                min(abs(e - a0) for a0 in anchors))
        coverage = ok / max(1, len(samples))
        mae = float(np.mean(errs)) if errs else 9999.0
        score = coverage - 0.0005 * mae  # coverage 우선, mae 보조

        if score > best_score:
            best_score, best_off, best_mae = score, δ, mae

    return int(best_off), max(0.0, best_score), float(best_mae)



# ---------- 열별 블록 추출(세로 연결요소) ----------
def _build_text_mask_for_col(df, x1: int, x2: int, y_top: int, y_bot: int, H: int, W: int) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    if df is None or len(df) == 0:
        return mask
    cx = df["left"] + df["width"] / 2
    cy = df["top"]  + df["height"] / 2
    sel = df[(cx >= x1) & (cx < x2) & (cy >= y_top) & (cy < y_bot)]
    for _, r in sel.iterrows():
        l = int(r["left"]); t = int(r["top"]); w = int(r["width"]); h = int(r["height"])
        pad_x = max(2, w // 10)
        pad_y = max(1, h // 10)
        xL = max(0, l - pad_x); xR = min(W-1, l + w + pad_x)
        yT = max(0, t - pad_y); yB = min(H-1, t + h + pad_y)
        mask[yT:yB+1, xL:xR+1] = 255
    return mask

def _build_color_mask(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    s = hsv[:, :, 1]
    mask_hsv = (s > COLOR_S_SAT).astype(np.uint8) * 255

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    a = lab[:, :, 1].astype(np.int16) - 128
    b = lab[:, :, 2].astype(np.int16) - 128
    chroma = np.sqrt(a*a + b*b)
    mask_lab = (chroma > COLOR_LAB_CHROMA).astype(np.uint8) * 255

    return cv2.max(mask_hsv, mask_lab)

def _content_mask_for_column(
    rgb: np.ndarray,
    df,
    x1: int, x2: int,
    y1: int, y2: int,
    H: int, W: int
) -> np.ndarray:
    roi_color = _build_color_mask(rgb[y1:y2, x1:x2])
    roi_text  = _build_text_mask_for_col(df, x1, x2, y1, y2, H, W)[y1:y2, x1:x2]
    roi = cv2.max(roi_color, roi_text)

    if OPEN_K > 0:
        roi = cv2.morphologyEx(roi, cv2.MORPH_OPEN,
                               cv2.getStructuringElement(cv2.MORPH_RECT, (OPEN_K, OPEN_K)),
                               iterations=1)
    if H_CLOSE_K > 0:
        roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_RECT, (H_CLOSE_K, 1)),
                               iterations=H_CLOSE_ITERS)
    out = np.zeros((H, W), dtype=np.uint8)
    out[y1:y2, x1:x2] = roi
    return out

def _components_from_mask(mask: np.ndarray, min_area: int) -> List[Tuple[int,int,int,int]]:
    H, W = mask.shape[:2]
    num, labels, stats, _ = cv2.connectedComponentsWithStats((mask>0).astype(np.uint8), connectivity=8)
    boxes = []
    for i in range(1, num):
        x, y, w, h, a = stats[i]
        if a < min_area:
            continue
        boxes.append((x, y, x+w, y+h))
    return boxes


# ---------------- 메인 파서 ----------------
def _parse_slots_from_image(binary_img: np.ndarray, rgb_img: np.ndarray) -> tuple[List[ParsedSlot], str]:
    H, W = rgb_img.shape[:2]
    debug_lines: List[str] = []

    # 1) 그리드 선
    y_lines, x_lines = _detect_grid_lines(binary_img)
    y_lines = [int(y) for y in list(y_lines or []) if y is not None and not (isinstance(y, float) and np.isnan(y))]
    x_lines = [int(x) for x in list(x_lines or []) if x is not None and not (isinstance(x, float) and np.isnan(x))]
    debug_lines.append(f"[LINE] x_lines={len(x_lines)}, y_lines={len(y_lines)}")

    # 2) OCR dataframe
    df = pytesseract.image_to_data(
        rgb_img, lang="kor+eng",
        config="--psm 6 -c preserve_interword_spaces=1",
        output_type=Output.DATAFRAME,
    ).dropna(subset=["text"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]
    df.to_csv("ocr_raw_debug.csv", index=False, encoding="utf-8-sig")

    header_h = int(H * 0.15)

    # 좌측 라벨 기반 time_w 초기 추정
    left = df.copy()
    left["cx"] = (left["left"] + left["width"] / 2).astype(int)
    mask_time = left["text"].str.contains(TIME_RE_CONTAINS, regex=True, na=False) & (left["top"] < int(H*0.85))
    time_w_guess = int(np.percentile(left.loc[mask_time, "cx"], 95)) + 10 if mask_time.any() else int(W*0.20)
    time_w_guess = max(int(W*0.10), min(time_w_guess, int(W*0.35)))
    debug_lines.append(f"[EST] time_w_guess={time_w_guess}")

    # 3) 열/요일 확정
    x_edges, days, time_w = _resolve_columns(df, rgb_img, W, H, header_h, x_lines, time_w_guess, debug_lines)
    C = max(1, len(x_edges) - 1)
    debug_lines.append(f"[EDGES-X] {x_edges} (C={C}) / days={days}")

    # 4) 행/시각 확정 + 시간 매핑 모델
    y_edges, row_starts = _resolve_rows(df, H, header_h, y_lines, time_w, debug_lines)
    R = max(1, len(y_edges) - 1)
    debug_lines.append(f"[EDGES-Y] len={len(y_edges)} (R={R})")
    debug_lines.append(f"[TIME] row_starts={row_starts}")

    if C < 2 or R < 2:
        debug_lines.append("[GUARD] edge/time insufficient → skip")
        return [], "\n".join(debug_lines)

    y0, hour_h = _hour_grid_model(y_edges)
    y0 = _refine_y0_with_left_labels(y0, hour_h, df, time_w, H)
    debug_lines.append(f"[MAP] y0={y0}, hour_h={hour_h:.2f}px (refined)")


    # 5) 1-pass: 요일별 박스 검출 + 원시 분단위 샘플 수집
    header_bottom = y_edges[1]
    time_right    = x_edges[1]
    min_area = int(W*H*AREA_MIN_FRACTION)

    day_boxes: Dict[str, List[Tuple[int,int,int,int]]] = defaultdict(list)
    day_samples: Dict[str, List[Tuple[float,float]]] = defaultdict(list)

    for c in range(1, C):
        x1, x2 = x_edges[c], x_edges[c+1]
        if x2 <= time_right:
            continue
        weekday = _weekday_for_column(c, days)
        if not weekday:
            continue
        col_mask = _content_mask_for_column(rgb_img, df, x1, x2, header_bottom, y_edges[-1], H, W)
        boxes = _components_from_mask(col_mask, min_area=min_area)
        debug_lines.append(f"[DAY {weekday}] comps={len(boxes)}")

        for (bx1, by1, bx2, by2) in boxes:
            y_top = max(by1, header_bottom+1)
            y_bot = min(by2, y_edges[-1]-1)
            if y_bot - y_top < 8:
                continue
            m_start = _y_to_minutes(y_top, y0, hour_h)
            m_end   = _y_to_minutes(y_bot, y0, hour_h)
            day_boxes[weekday].append((bx1, y_top, bx2, y_bot))
            day_samples[weekday].append((m_start, m_end))

    # 6) 요일별 오프셋 δ 추정
    day_offsets: Dict[str, int] = {}
    for d in day_boxes.keys():
        step = DAY_STEP_MINUTES.get(d, 60)
        off, cov, mae = _estimate_offset_for_day(day_samples.get(d, []), step)
        day_offsets[d] = off
        debug_lines.append(f"[ANCHOR {d}] step={step}min, offset={off}min (coverage={cov:.2f}, mae={mae:.1f})")

    # 7) 2-pass: 스냅 + OCR 추출 → 슬롯 생성
    slots: List[ParsedSlot] = []

    def _collect_from_roi(x1: int, y1: int, x2: int, y2: int) -> Tuple[str, Optional[str], Optional[str], str]:
        try:
            Hh, Ww = rgb_img.shape[:2]
            pad = 6
            x1p = max(x1+pad, 0); y1p = max(y1+pad, 0)
            x2p = min(x2-pad, Ww-1); y2p = min(y2-pad, Hh-1)
            crop = rgb_img[y1p:y2p, x1p:x2p]
            if crop.size == 0:
                return "", None, None, ""

            gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
            bin_roi = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            txt6 = _ocr_string(bin_roi, psm=6)
            lines = [t.strip() for t in txt6.splitlines() if t.strip()]

            txt7 = _ocr_string(bin_roi, psm=7)
            lines += [t.strip() for t in txt7.splitlines() if t.strip()]
            lines = list(dict.fromkeys(lines))

            try:
                roi_df = pytesseract.image_to_data(
                    crop, lang="kor+eng", config="--psm 6 -c preserve_interword_spaces=1",
                    output_type=Output.DATAFRAME,
                )
            except Exception:
                roi_df = None

            if roi_df is not None:
                roi_df = roi_df.dropna(subset=["text"])
                if len(roi_df) > 0:
                    words = [{
                        "text": str(r["text"]).strip(),
                        "left": int(r["left"]),
                        "top": int(r["top"]),
                        "width": int(r["width"]),
                        "height": int(r["height"])
                    } for _, r in roi_df.iterrows() if str(r["text"]).strip()]
                    rec = _reconstruct_lines_by_yx(words)
                    ver = _fuse_vertical_hangul(words)
                    cand = list(dict.fromkeys(rec + ver))
                    norm, seen = [], set()
                    for s in cand:
                        s = TIME_RE.sub("", s).strip()
                        if not s: continue
                        s = _normalize_line(s)
                        if s and s not in seen:
                            seen.add(s); norm.append(s)
                    if norm:
                        lines = norm

            line_freq = Counter(re.sub(r'^\ \[V\]', '', z) for z in lines)
            title, prof, loc, raw = _choose_fields_from_lines(lines, line_freq)
            raw = "\n".join(re.sub(r'^\ \[V\]', '', t) for t in lines)
            return title or "", prof, loc, raw or ""
        except Exception as e:
            logger.exception("collect_from_roi failed: %s", e)
            return "", None, None, ""

    for d, boxes in day_boxes.items():
        step = DAY_STEP_MINUTES.get(d, 60)
        δ = int(day_offsets.get(d, 0))
        anchors = _anchors_for_weekday(d, δ)
        for (bx1, y_top, bx2, y_bot) in boxes:
            m_start = _y_to_minutes(y_top, y0, hour_h)
            m_end   = _y_to_minutes(y_bot, y0, hour_h)

            s_snap = _snap_to_anchors(m_start, anchors, SNAP_TOL_PRIMARY)
            e_snap = _snap_to_anchors(m_end,   anchors, SNAP_TOL_PRIMARY)

            if s_snap is None:
                s_snap = _snap_to_anchors(m_start, anchors, SNAP_TOL_RELAXED)
            if e_snap is None:
                e_snap = _snap_to_anchors(m_end, anchors, SNAP_TOL_RELAXED)

            # 최종 안전망: step 기준 라운드
            if s_snap is None: s_snap = _round_by_step(m_start, step)
            if e_snap is None: e_snap = _round_by_step(m_end,   step)

            if e_snap <= s_snap:
                e_snap = s_snap + step  # 최소 한 그리드 보장

            start_hhmm = _minutes_to_hhmm(s_snap)
            end_hhmm   = _minutes_to_hhmm(e_snap)

            t, p, l, raw = _collect_from_roi(bx1, y_top, bx2, y_bot)
            if not t:
                t = ""  # 제목 비어도 블록은 유지

            slots.append(ParsedSlot(
                weekday=d,
                start_time=start_hhmm,
                end_time=end_hhmm,
                title=t, professor=p, location=l, raw_text=raw
            ))
            debug_lines.append(f"[SNAP {d}] ({y_top},{y_bot})px → {start_hhmm}~{end_hhmm} title='{t}' (δ={δ})")

    if ENABLE_DEDUPE:
        slots = _dedupe_adjacent_by_support(slots, days, row_starts, x_edges, y_edges, df, rgb_img)

    slots = [s for s in slots if s.weekday and s.start_time]
    slots = sorted(slots, key=lambda s: (s.weekday, s.start_time, s.end_time or ""))

    if not DISABLE_FINAL_MERGE:
        slots = _merge_contiguous_slots(slots)

    return slots, "\n".join(debug_lines)


def _dedupe_adjacent_by_support(
    slots: List[ParsedSlot],
    days: List[str],
    row_starts: List[str],
    x_edges: List[int],
    y_edges: List[int],
    df,
    rgb_img: np.ndarray
) -> List[ParsedSlot]:
    if not slots or not days or not row_starts or len(x_edges) < 3 or len(y_edges) < 3:
        return slots

    day_to_c = {d: i+1 for i, d in enumerate(days)}  # 시간열 0, 요일 1~

    from collections import defaultdict as _dd
    buckets = _dd(list)
    for s in slots:
        key = (s.weekday, s.title.strip(), s.start_time, s.end_time or "", s.location or "")
        buckets[key].append(s)

    def _row_index(t: str) -> int:
        try:
            return row_starts.index(t) + 1
        except ValueError:
            return -1

    keep = set()
    for _, arr in buckets.items():
        if len(arr) == 1:
            keep.add(id(arr[0])); continue

        scored = []
        for s in arr:
            c = day_to_c.get(s.weekday, -1)
            r1 = _row_index(s.start_time)
            r2 = _row_index(s.end_time) if s.end_time else r1
            if c < 1 or (c+1) >= len(x_edges) or r1 < 1 or r2 < r1 or (len(y_edges) < 2):
                score = 0.0
            else:
                mean_fill, ko_sum = 0.0, 0
                x1, x2 = x_edges[c], x_edges[c+1]
                r2_clip = min(r2, len(y_edges)-2)
                for r in range(r1, r2_clip+1):
                    y1, y2 = y_edges[r], y_edges[r+1]
                    mean_fill += _cell_fill_ratio(rgb_img, x1, y1, x2, y2)
                    w = max(1, x2 - x1); shrink = max(int(w*0.10), 6)
                    sx1, sx2 = (x1+shrink, x2-shrink) if (x2-x1) > 2*shrink else (x1, x2)
                    cx = df["left"] + df["width"]/2; cy = df["top"] + df["height"]/2
                    mask = (cx >= sx1) & (cx < sx2) & (cy >= y1) & (cy < y2)
                    if mask.any():
                        sel = df.loc[mask, "text"].astype(str)
                        ko_sum += int(sel.str.count(r'[가-힣]').sum())
                denom = max(1, (r2_clip - r1 + 1))
                mean_fill = mean_fill / denom
                score = mean_fill + 0.03 * ko_sum
            scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        keep.add(id(scored[0][1]))

    return [s for s in slots if id(s) in keep]


# ---------------- 파일/이미지 엔트리 ----------------
def _pdf_to_images(pdf_path: str | Path) -> list[Image.Image]:
    out = []
    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=220)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            out.append(img)
    return out


def _parse_image_timetable(pil_img: Image.Image) -> tuple[List[ParsedSlot], str]:
    rgb = np.array(pil_img.convert("RGB"))
    binary = _binarize(rgb)
    return _parse_slots_from_image(binary, rgb)


# 공개 API
def parse_timetable_from_file(file_path: str | Path) -> tuple[List[ParsedSlot], str]:
    fp = Path(file_path)
    images: list[Image.Image] = []
    if fp.suffix.lower() == ".pdf":
        images.extend(_pdf_to_images(fp))
    else:
        images.append(Image.open(fp))

    all_slots, all_raw = [], []
    for img in images:
        rgb = np.array(img.convert("RGB"))
        binary = _binarize(rgb)
        slots, raw = _parse_slots_from_image(binary, rgb)
        all_slots.extend(slots)
        all_raw.append(raw)

    all_slots = sorted(all_slots, key=lambda s: (s.weekday, s.start_time, s.end_time or ""))

    if not DISABLE_FINAL_MERGE:
        all_slots = _merge_contiguous_slots(all_slots)

    return all_slots, "\n---\n".join(all_raw)

def parse_timetable_from_pdf(pdf_path: str | Path) -> tuple[List[ParsedSlot], str]:
    return parse_timetable_from_file(pdf_path)

def parse_timetable_from_image(img_path: str | Path) -> tuple[List[ParsedSlot], str]:
    return parse_timetable_from_file(img_path)


def create_schedule_files(slots: List[ParsedSlot], base_path: str | Path = "schedule_output"):
    """
    파싱된 시간표 슬롯 리스트를 바탕으로 과목별 폴더와 강의별 메모장 파일을 생성합니다.

    :param slots: parse_timetable_from_file()로부터 반환된 ParsedSlot 객체의 리스트
    :param base_path: 모든 과목 폴더가 생성될 최상위 경로
    """
    base_dir = Path(base_path)
    base_dir.mkdir(exist_ok=True)
    
    # 파일 이름으로 사용하기 부적절한 문자 제거를 위한 정규식
    invalid_chars = re.compile(r'[\\/:*?"<>|]')
    
    created_files = []

    for slot in slots:
        # 1. 과목명으로 폴더 경로 생성
        subject_title = slot.title.strip() if slot.title else "기타"
        sanitized_folder_name = invalid_chars.sub("", subject_title)
        if not sanitized_folder_name:
            sanitized_folder_name = "기타"
        
        subject_dir = base_dir / sanitized_folder_name
        subject_dir.mkdir(exist_ok=True)
        
        # 2. 파일명 생성 (예: 09_00-10_30_월.txt)
        start_str = slot.start_time.replace(":", "_")
        end_str = slot.end_time.replace(":", "_") if slot.end_time else ""
        filename = f"{start_str}-{end_str}_{slot.weekday}.txt"
        
        file_path = subject_dir / filename
        
        # 3. 파일 내용 작성
        content = []
        content.append(f"과목: {slot.title or 'N/A'}")
        content.append(f"시간: {slot.start_time} ~ {slot.end_time or 'N/A'}")
        content.append(f"요일: {slot.weekday or 'N/A'}")
        content.append(f"교수: {slot.professor or 'N/A'}")
        content.append(f"강의실: {slot.location or 'N/A'}")
        content.append("\n---\n")
        content.append(f"[원본 OCR 텍스트]\n{slot.raw_text or ''}")
        
        # 4. 파일 쓰기
        try:
            file_path.write_text("\n".join(content), encoding="utf-8")
            created_files.append(str(file_path))
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")

    logger.info(f"{len(created_files)}개의 파일을 성공적으로 생성했습니다. 경로: {base_dir.resolve()}")
    return created_files

