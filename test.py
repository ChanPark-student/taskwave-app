# step1_preprocess.py
# ------------------------------------------------------------
# 시간표 이미지 1장을 로드해 전처리(블러, Gray/HSV 변환)하고
# 디버그 이미지를 저장한다.
# - 유니코드 경로(한글 파일명) 안전하게 처리
# - 원본/gray/H/S/V 및 간단한 대비보정본 저장
# ------------------------------------------------------------

import argparse
import os
import sys
from pathlib import Path
import numpy as np
import cv2
from datetime import datetime

# --------- 유틸: 유니코드 경로 대응 imread/imwrite ---------
def imread_unicode(path: str, flags=cv2.IMREAD_COLOR):
    """Windows에서도 한글 경로 안전하게 읽기"""
    path = str(path)
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, flags)
    if img is None:
        raise FileNotFoundError(f"이미지를 열 수 없습니다: {path}")
    return img

def imwrite_unicode(path: str, img) -> None:
    """Windows에서도 한글 경로 안전하게 쓰기"""
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    if ext == "":
        ext = ".png"
        path += ext
    success, buf = cv2.imencode(ext, img)
    if not success:
        raise RuntimeError(f"이미지 인코딩 실패: {path}")
    buf.tofile(path)

def ensure_dir(d: str | Path) -> Path:
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    return p

# --------- 전처리 루틴 ---------
def preprocess(img_bgr: np.ndarray, max_width: int = 2400):
    """
    - 필요시 리사이즈(가로 최대 max_width 유지)
    - 약한 노이즈 제거(미디언 블러 3)
    - Gray/HSV 변환
    - CLAHE(대비 보정)로 OCR 친화 그레이 버전도 생성
    """
    h, w = img_bgr.shape[:2]
    scale = 1.0
    if w > max_width:
        scale = max_width / w
        img_bgr = cv2.resize(img_bgr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

    # 약한 노이즈 제거
    denoised = cv2.medianBlur(img_bgr, 3)

    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(denoised, cv2.COLOR_BGR2HSV)
    h_ch, s_ch, v_ch = cv2.split(hsv)

    # OCR 친화 그레이(선택): CLAHE + 가벼운 샤픈
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)

    # 샤픈(약하게)
    k = np.array([[0, -1, 0],
                  [-1, 5, -1],
                  [0, -1, 0]], dtype=np.float32)
    gray_clahe_sharp = cv2.filter2D(gray_clahe, -1, k)

    return {
        "bgr": img_bgr,
        "denoised": denoised,
        "gray": gray,
        "h": h_ch,
        "s": s_ch,
        "v": v_ch,
        "gray_clahe": gray_clahe,
        "gray_clahe_sharp": gray_clahe_sharp,
        "scale": scale,
    }

def make_quick_preview(panel_dict: dict) -> np.ndarray:
    """
    원본/gray/H/S/V를 2x3 콜라주로 합쳐 빠르게 점검할 수 있는 미리보기 생성
    """
    def to3c(x):
        return cv2.cvtColor(x, cv2.COLOR_GRAY2BGR) if len(x.shape) == 2 else x

    tiles = [
        ("orig", panel_dict["bgr"]),
        ("gray", panel_dict["gray"]),
        ("H", panel_dict["h"]),
        ("S", panel_dict["s"]),
        ("V", panel_dict["v"]),
        ("clahe", panel_dict["gray_clahe_sharp"]),
    ]

    # 같은 폭으로 리사이즈
    target_w = 800
    resized = []
    for name, im in tiles:
        im3 = to3c(im)
        h, w = im3.shape[:2]
        if w != target_w:
            r = target_w / w
            im3 = cv2.resize(im3, (target_w, int(h*r)), interpolation=cv2.INTER_AREA)
        # 라벨 워터마크
        overlay = im3.copy()
        cv2.rectangle(overlay, (0, 0), (180, 40), (0, 0, 0), -1)
        im3 = cv2.addWeighted(overlay, 0.25, im3, 0.75, 0)
        cv2.putText(im3, name, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        resized.append(im3)

    # 2x3 배치
    row1 = np.hstack(resized[0:3])
    row2 = np.hstack(resized[3:6])
    collage = np.vstack([row1, row2])
    return collage

# --------- 메인 ---------
def main():
    parser = argparse.ArgumentParser(description="Step1: 시간표 이미지 전처리 디버그")
    parser.add_argument("--image", required=True, help="C:/Users/211833/Desktop/스크린샷 2025-08-13 003824.png")
    parser.add_argument("--out", default=None, help="C:/Users/211833/Desktop")
    parser.add_argument("--max_width", type=int, default=2400, help="전처리용 최대 가로 해상도")
    args = parser.parse_args()

    out_dir = args.out or f"step1_out_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_path = ensure_dir(out_dir)

    print(f"[i] 입력: {args.image}")
    print(f"[i] 출력 폴더: {out_path}")

    img = imread_unicode(args.image)
    print(f"[i] 원본 크기: {img.shape[1]}x{img.shape[0]}")

    panels = preprocess(img, max_width=args.max_width)

    # 개별 저장
    imwrite_unicode(out_path / "00_original.png", panels["bgr"])
    imwrite_unicode(out_path / "01_denoised.png", panels["denoised"])
    imwrite_unicode(out_path / "02_gray.png", panels["gray"])
    imwrite_unicode(out_path / "03_h.png", panels["h"])
    imwrite_unicode(out_path / "04_s.png", panels["s"])
    imwrite_unicode(out_path / "05_v.png", panels["v"])
    imwrite_unicode(out_path / "06_gray_clahe.png", panels["gray_clahe"])
    imwrite_unicode(out_path / "07_gray_clahe_sharp.png", panels["gray_clahe_sharp"])

    # 미리보기 콜라주
    preview = make_quick_preview(panels)
    imwrite_unicode(out_path / "preview_collage.png", preview)

    print("[✓] 저장 완료:")
    for name in ["00_original.png", "01_denoised.png", "02_gray.png", "03_h.png",
                 "04_s.png", "05_v.png", "06_gray_clahe.png", "07_gray_clahe_sharp.png",
                 "preview_collage.png"]:
        print(f"   - {out_path / name}")

    print("\n다음 단계 힌트:")
    print(" - 2단계(블록 후보 추출): HSV에서 S,V 임계로 배경 제외 마스크 → 컨투어 → bbox")
    print(" - 3단계(요일 컬럼): 상단 헤더 OCR 또는 x중심 KMeans로 5컬럼 분류")
    print(" - 4~5단계(시간 라인): HoughLinesP로 가로라인 + 좌측 '오전/오후 n시' OCR로 보정")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[에러] {e}", file=sys.stderr)
        sys.exit(1)
