# step2_detect_blocks_color.py
# 색상 클러스터링으로 같은 수업(같은 파스텔톤)을 묶어 블록 추출
# 사용 예시:
# .\.venv\Scripts\python.exe .\step2_detect_blocks_color.py ^
#   --image "C:\Users\211833\Desktop\스크린샷 2025-08-13 003824.png" ^
#   --out ".\step2_out_color"

import argparse, os, sys, json
from pathlib import Path
from typing import List, Tuple
import numpy as np
import cv2

# ---------- 공용 IO ----------
def imread_unicode(p: str, flags=cv2.IMREAD_COLOR):
    data = np.fromfile(str(p), dtype=np.uint8)
    img = cv2.imdecode(data, flags)
    if img is None:
        raise FileNotFoundError(p)
    return img

def imwrite_unicode(p: str | Path, img):
    p = str(p)
    ext = os.path.splitext(p)[1].lower() or ".png"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError(f"encode fail: {p}")
    buf.tofile(p)

def ensure_dir(d: str | Path) -> Path:
    d = Path(d); d.mkdir(parents=True, exist_ok=True); return d

# ---------- 유틸 ----------
def preprocess(img, max_width=2400):
    h, w = img.shape[:2]
    if w > max_width:
        r = max_width / w
        img = cv2.resize(img, (int(w*r), int(h*r)), interpolation=cv2.INTER_AREA)
    return cv2.medianBlur(img, 3)

def build_color_mask(img, s_thresh=15, v_min=150):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)
    bright = V > 200
    s90 = np.percentile(S[bright], 90) if bright.sum() > 500 else np.percentile(S, 90)
    s_thr = max(s_thresh, int(np.clip(s90*0.5, 12, 40)))
    mask = ((S >= s_thr) & (V >= v_min)).astype(np.uint8)*255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  cv2.getStructuringElement(cv2.MORPH_RECT, (3,3)), 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5,5)), 1)
    return mask, s_thr

def find_components(mask, img_shape, min_area_ratio=0.0009, min_w=50, min_h=30):
    H, W = img_shape[:2]
    min_area = int(H*W*min_area_ratio)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    comps=[]
    for c in cnts:
        x,y,w,h = cv2.boundingRect(c)
        if w*h < min_area or w < min_w or h < min_h:
            continue
        pad=3
        x=max(0,x-pad); y=max(0,y-pad)
        w=min(W-x,w+pad*2); h=min(H-y,h+pad*2)
        comps.append((x,y,w,h))
    comps.sort(key=lambda b:(b[1],b[0]))
    return comps

def estimate_content_x_range(mask):
    colsum = (mask>0).sum(axis=0)
    xs = np.where(colsum > int(mask.shape[0]*0.02))[0]
    return (0, mask.shape[1]-1) if len(xs)==0 else (int(xs.min()), int(xs.max()))

def make_columns(x0,x1,n=5):
    w = x1-x0
    cuts=[int(x0+i*w/n) for i in range(1,n)]
    edges=[x0]+cuts+[x1]
    return [(edges[i], edges[i+1]) for i in range(n)]  # [(l,r),...]

def assign_weekday(xc:int, cols:List[Tuple[int,int]]):
    names=["월","화","수","목","금"]
    best=10**9; idx=0
    for i,(l,r) in enumerate(cols):
        c=(l+r)//2; d=abs(xc-c)
        if d<best: best=d; idx=i
    return idx, names[idx]

def v_overlap(a,b):
    ax,ay,aw,ah=a; bx,by,bw,bh=b
    y1=max(ay,by); y2=min(ay+ah, by+bh)
    inter=max(0, y2-y1)
    return inter/max(1, min(ah,bh))

def union(a,b):
    ax,ay,aw,ah=a; bx,by,bw,bh=b
    x1=min(ax,bx); y1=min(ay,by)
    x2=max(ax+aw, bx+bw); y2=max(ay+ah, by+bh)
    return (x1,y1,x2-x1,y2-y1)

def text_density(img, bbox, top_ratio=0.5):
    x,y,w,h = bbox
    h_top = max(20, int(h*top_ratio))
    roi = img[y:y+h_top, x:x+w]
    g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    g = cv2.medianBlur(g, 3)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT,(2,2)), 1)
    return float((th>0).sum())/float(max(1,th.size))

# ---------- 색상 특징 ----------
def comp_feature_hsv(img, mask, bbox):
    x,y,w,h = bbox
    roi = img[y:y+h, x:x+w]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV).astype(np.float32)
    # 마스크로 색 영역만 평균내기
    mroi = mask[y:y+h, x:x+w]
    if mroi.size == 0:
        H = hsv[...,0].reshape(-1); S=hsv[...,1].reshape(-1); V=hsv[...,2].reshape(-1)
    else:
        idx = mroi>0
        if idx.sum() < 10:
            H = hsv[...,0].reshape(-1); S=hsv[...,1].reshape(-1); V=hsv[...,2].reshape(-1)
        else:
            H = hsv[...,0][idx]; S=hsv[...,1][idx]; V=hsv[...,2][idx]
    h_mean = float(np.mean(H))
    s_mean = float(np.mean(S))
    v_mean = float(np.mean(V))
    # Hue 원형 좌표로 투영
    ang = h_mean / 180.0 * 2*np.pi
    hcos, hsin = np.cos(ang), np.sin(ang)
    # 스케일링
    return np.array([hcos, hsin, s_mean/255.0, v_mean/255.0], dtype=np.float32), (h_mean, s_mean, v_mean)

# ---------- k-means(K 자동) ----------
def choose_k_by_elbow(img_feats: np.ndarray, k_min=5, k_max=9, rel_drop=0.10):
    # N = 후보 요소 수
    N = int(img_feats.shape[0])
    if N <= 1:
        # 요소가 1개 이하라면 군집 하나로 처리
        return 1, np.zeros((N,), dtype=np.int32)

    # k 범위를 N 이하로 조정
    k_max = max(1, min(k_max, N))
    k_min = max(1, min(k_min, k_max))

    last = None
    best_k = k_min
    for k in range(k_min, k_max + 1):
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1e-4)
        compactness, labels, centers = cv2.kmeans(
            img_feats.astype(np.float32), k, None, crit, 5, cv2.KMEANS_PP_CENTERS
        )
        if last is not None:
            drop = (last - compactness) / max(1e-6, last)
            if drop < rel_drop:
                best_k = max(k_min, k - 1)
                break
        last = compactness
        best_k = k

    # 최종 K로 재학습
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 80, 1e-4)
    compactness, labels, centers = cv2.kmeans(
        img_feats.astype(np.float32), best_k, None, crit, 8, cv2.KMEANS_PP_CENTERS
    )
    return best_k, labels.flatten()


# ---------- 파이프라인 ----------
def run(image_path, out_dir,
        max_width=2400, s_thresh=15, v_min=150,
        min_area_ratio=0.0009, min_w=50, min_h=30,
        k_min=5, k_max=9, rel_drop=0.10,
        merge_gap_frac=0.08, min_w_frac=0.30,
        drop_text_density=0.0015, thin_w_frac=0.45,
        expand_pad_frac=0.03):
    out = ensure_dir(out_dir)
    img = imread_unicode(image_path)
    img = preprocess(img, max_width)
    H_img, W_img = img.shape[:2]

    mask, used_s = build_color_mask(img, s_thresh, v_min)
    imwrite_unicode(out/"mask_raw.png", mask)

    comps = find_components(mask, img.shape, min_area_ratio, min_w, min_h)
    if not comps:
        raise RuntimeError("색 후보 컴포넌트를 찾지 못했습니다.")

    # 컨텐츠 가로 범위 -> 5 칼럼
    x0,x1 = estimate_content_x_range(mask)
    cols = make_columns(x0, x1, 5)
    col_w = np.mean([r-l for (l,r) in cols])
    merge_gap = int(col_w * merge_gap_frac)
    min_w_px  = int(col_w * min_w_frac)
    thin_w_px = int(col_w * thin_w_frac)
    pad_px    = int(col_w * expand_pad_frac)

    # 각 컴포넌트의 색 특징 계산
    feats = []
    avghsv = []
    for b in comps:
        f, hsv = comp_feature_hsv(img, mask, b)
        feats.append(f); avghsv.append(hsv)
    feats = np.vstack(feats)

    # K 자동 선택 + k-means
    k, labels = choose_k_by_elbow(feats, k_min, k_max, rel_drop)

    # 클러스터별로 모으기
    by_cluster = {i: [] for i in range(k)}
    for b, lab in zip(comps, labels.tolist()):
        by_cluster[lab].append(b)

    # 같은 색(클러스터) 안에서 요일별로 분리·병합
    def clip_to_col(b, l, r):
        x,y,w,h = b
        nx = max(x, l+pad_px)
        rx = min(x+w, r-pad_px)
        if rx <= nx: return None
        return (nx, y, rx-nx, h)

    def merge_horizontal(lst):
        if not lst: return []
        lst.sort(key=lambda b:(b[1],b[0]))
        merged=[lst[0]]
        for b in lst[1:]:
            a=merged[-1]
            gap = b[0] - (a[0]+a[2])
            if gap <= merge_gap and v_overlap(a,b) >= 0.85:
                merged[-1] = union(a,b)
            else:
                merged.append(b)
        return merged

    results_boxes=[]
    for ci in range(k):
        parts = by_cluster[ci]
        # 요일별 바구니
        buckets = {d:[] for d in range(5)}
        for b in parts:
            xc = b[0]+b[2]//2
            d,_ = assign_weekday(xc, cols)
            l,r = cols[d]
            cb = clip_to_col(b, l, r)
            if cb is not None:
                buckets[d].append(cb)

        # 얇은/저밀도 조각 제거·병합 후 확정
        for d in range(5):
            xs = buckets[d]
            if not xs: continue
            # 너무 얇고 텍스트가 거의 없는 조각 제거
            keep=[]
            for b in xs:
                if b[2] < thin_w_px and text_density(img, b) < drop_text_density:
                    continue
                keep.append(b)
            xs = keep
            xs = merge_horizontal(xs)
            # 같은 줄에서 또 합쳐지지 않은 것들 추가 병합(2회)
            xs = merge_horizontal(xs)
            results_boxes.extend([(b,d) for b in xs])

    # 요일별 최종 박스 정리
    final=[]
    for (b,d) in results_boxes:
        final.append((b,d))
    # 포함 억제(같은 요일): 큰 박스가 작은 박스를 완전히 포함하면 텍스트 적은 쪽 제거
    def suppress(day_items):
        if not day_items: return []
        boxes=[it[0] for it in day_items]
        dens=[text_density(img,b) for b in boxes]
        keep=[True]*len(boxes)
        for i in range(len(boxes)):
            if not keep[i]: continue
            for j in range(len(boxes)):
                if i==j or not keep[j]: continue
                A=boxes[i]; B=boxes[j]
                # 거의 포함 & 세로겹침 높음
                ax,ay,aw,ah=A; bx,by,bw,bh=B
                if (ax-3 <= bx and ay-3 <= by and ax+aw+3 >= bx+bw and ay+ah+3 >= by+bh) and v_overlap(A,B)>=0.9:
                    if dens[i] <= dens[j]: keep[i]=False
                    else: keep[j]=False
        return [day_items[i] for i,kp in enumerate(keep) if kp]

    grouped = {d:[] for d in range(5)}
    for b,d in final:
        grouped[d].append((b,d))
    cleaned=[]
    for d in range(5):
        cleaned += suppress(grouped[d])

    # 라벨링 + 저장
    cleaned.sort(key=lambda it:(it[1], it[0][1], it[0][0]))
    entries=[]
    for (x,y,w,h), d in cleaned:
        idx, name = d, ["월","화","수","목","금"][d]
        entries.append(((x,y,w,h), idx, name))

    # 시각화
    vis = img.copy(); ov = img.copy()
    for i,(b,idx,name) in enumerate(entries,1):
        x,y,w,h = b
        cv2.rectangle(ov,(x,y),(x+w,y+h),(0,255,255),-1)
        cv2.rectangle(vis,(x,y),(x+w,y+h),(0,140,255),2)
        cv2.putText(vis, f"#{i} {name}", (x+6,y+24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,90,255), 2, cv2.LINE_AA)
    overlay = cv2.addWeighted(ov, 0.25, vis, 0.75, 0)
    imwrite_unicode(out/"overlay_blocks.png", overlay)

    # JSON
    out_json = out/"blocks_stage2.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(entries),
            "blocks": [
                {"bbox":[int(b[0]),int(b[1]),int(b[2]),int(b[3])],
                 "weekday_idx": int(idx), "weekday": name,
                 "raw_text":"", "subject": ""} for (b,idx,name) in entries
            ],
            "used_s_thresh": int(used_s),
            "k_chosen": int(k)
        }, f, ensure_ascii=False, indent=2)

    print(f"[✓] 색상기반 블록 수: {len(entries)}  (k={k}, S임계={used_s})")
    print(f" - mask:    {out/'mask_raw.png'}")
    print(f" - overlay: {out/'overlay_blocks.png'}")
    print(f" - json:    {out_json}")

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="색상 클러스터링으로 시간표 블록 검출")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", default="step2_out_color")
    ap.add_argument("--max_width", type=int, default=2400)
    ap.add_argument("--s_thresh", type=int, default=15)
    ap.add_argument("--v_min", type=int, default=150)
    ap.add_argument("--min_area_ratio", type=float, default=0.0009)
    ap.add_argument("--min_w", type=int, default=50)
    ap.add_argument("--min_h", type=int, default=30)
    ap.add_argument("--k_min", type=int, default=5)
    ap.add_argument("--k_max", type=int, default=9)
    ap.add_argument("--rel_drop", type=float, default=0.10, help="elbow: 개선율 임계")
    ap.add_argument("--merge_gap_frac", type=float, default=0.08)
    ap.add_argument("--min_w_frac", type=float, default=0.30)
    ap.add_argument("--drop_text_density", type=float, default=0.0015)
    ap.add_argument("--thin_w_frac", type=float, default=0.45)
    ap.add_argument("--expand_pad_frac", type=float, default=0.03)
    args = ap.parse_args()

    run(args.image, args.out,
        args.max_width, args.s_thresh, args.v_min,
        args.min_area_ratio, args.min_w, args.min_h,
        args.k_min, args.k_max, args.rel_drop,
        args.merge_gap_frac, args.min_w_frac,
        args.drop_text_density, args.thin_w_frac, args.expand_pad_frac)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[에러] {e}", file=sys.stderr); sys.exit(1)
