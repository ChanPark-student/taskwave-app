"""
Requirements:
  pip install requests opencv-python pillow numpy

Env vars:
  export KAKAO_REST_KEY="YOUR_KAKAO_REST_KEY"
  export MAPILLARY_TOKEN="MLY|YOUR_MAPILLARY_ACCESS_TOKEN"

What it does:
  1) 카카오 길찾기 API로 '밀양역 → 동대구역' 경로를 가져온다.
  2) 경로를 일정 간격(기본 150m)으로 샘플링한다.
  3) 각 지점 주변의 Mapillary 이미지를 bbox로 검색해 가장 가까운 1장을 받는다(thumb_1024).
  4) 이미지를 순서대로 이어 붙여 MP4 영상을 만든다.
  5) 카카오 가이드 포인트(우회전/좌회전 등) 근처 프레임은 약간 느리게(프레임 3배) 반복해 강조한다.

Note:
  - 데모 목적: 커버리지가 부족하면 일부 포인트는 스킵된다(그럴 경우 자동으로 더 큰 bbox로 재시도).
  - Mapillary Terms/Attribution을 준수하세요. 프레임 하단에 간단한 Attribution 오버레이를 추가함.
"""

import os, math, json, time, tempfile, shutil, pathlib
import requests
import cv2
import numpy as np

# ---------- CONFIG ----------
KAKAO_KEY = os.environ.get("KAKAO_REST_KEY")
MAPILLARY_TOKEN = os.environ.get("MAPILLARY_TOKEN")

# Miryang Station (origin) and Dongdaegu Station (destination)
ORIGIN = {"lon": 128.7711, "lat": 35.4745}   # 밀양역 도로 근처
DEST = {"lon": 128.6287, "lat": 35.8800}  # 도로 위 지점

SAMPLE_EVERY_M = 150          # 경로 샘플 간격(m)
BBOX_START_DEG = 0.0005       # 약 55m 근방(위도 기준). 실패 시 확대 재시도
BBOX_MAX_DEG   = 0.003        # 최대 ~330m
VIDEO_FPS      = 8
OUT_MP4        = "miryang_to_dongdaegu.mp4"
# ----------------------------

assert KAKAO_KEY, "KAKAO_REST_KEY env var required"
assert MAPILLARY_TOKEN, "MAPILLARY_TOKEN env var required"

def haversine_m(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def get_route_vertices_and_guides(origin, dest):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    params = {
    "origin": f"{origin['lon']},{origin['lat']}",
    "destination": f"{dest['lon']},{dest['lat']}",
    "priority": "RECOMMEND",
    "car_fuel": "GASOLINE",
    "car_hipass": "false",
    "summary": "false",
    "alternatives": "false",
    "road_details": "false"
}

    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}", "Content-Type": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    routes = data.get("routes", [])
    if not routes:
        raise RuntimeError("No route found from Kakao Directions API.")
    route = routes[0]

    # roads[].vertexes is a flat list [x0,y0,x1,y1,...], concatenate for all sections/roads
    vertices = []
    guides = []  # list of dicts: {lon,lat,guidance,type}
    for sec in route.get("sections", []):
        for road in sec.get("roads", []):
            v = road.get("vertexes", [])
            # pair (x=lon, y=lat)
            for i in range(0, len(v), 2):
                vertices.append((v[i], v[i+1]))
        for g in sec.get("guides", []):
            guides.append({"lon": g["x"], "lat": g["y"], "guidance": g.get("guidance", ""), "type": g.get("type")})

    # deduplicate consecutive identical points
    dedup = []
    for p in vertices:
        if not dedup or p != dedup[-1]:
            dedup.append(p)
    return dedup, guides

def sample_along_path(vertices, step_m=SAMPLE_EVERY_M):
    sampled = []
    if not vertices:
        return sampled
    acc = 0.0
    sampled.append(vertices[0])
    for i in range(1, len(vertices)):
        lon1, lat1 = vertices[i-1]
        lon2, lat2 = vertices[i]
        seg_len = haversine_m(lon1, lat1, lon2, lat2)
        if seg_len == 0:
            continue
        t = step_m - acc
        while t <= seg_len:
            ratio = t / seg_len
            lon = lon1 + (lon2 - lon1) * ratio
            lat = lat1 + (lat2 - lat1) * ratio
            sampled.append((lon, lat))
            t += step_m
        acc = (seg_len - (t - step_m))
    if sampled[-1] != vertices[-1]:
        sampled.append(vertices[-1])
    return sampled

def mapillary_nearest_image(lon, lat, bbox_deg, token):
    """Try to get a thumb_1024_url near lon/lat by querying a small bbox."""
    params = {
        "access_token": token,
        "bbox": f"{lon-bbox_deg},{lat-bbox_deg},{lon+bbox_deg},{lat+bbox_deg}",
        "fields": "id,thumb_1024_url,computed_geometry,captured_at,sequence",
        "limit": 1,
    }
    r = requests.get("https://graph.mapillary.com/images", params=params, timeout=20)
    if r.status_code != 200:
        return None
    js = r.json()
    arr = js.get("data", [])
    if not arr:
        return None
    return arr[0]  # dict with thumb_1024_url

def download_image(url, path):
    for _ in range(3):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            time.sleep(0.4)
    return False

def nearest_index(points, target):
    # Return index of point closest to target (lon,lat)
    best_i, best_d = None, 1e18
    tlon, tlat = target
    for i,(lon,lat) in enumerate(points):
        d = haversine_m(lon,lat, tlon,tlat)
        if d < best_d:
            best_d, best_i = d, i
    return best_i

def build_video_from_images(img_paths, out_path, slow_indices=set(), fps=VIDEO_FPS):
    if not img_paths:
        raise RuntimeError("No frames to write.")
    # read first valid image
    first = None
    for p in img_paths:
        if p and os.path.exists(p):
            first = p
            break
    if not first:
        raise RuntimeError("No valid images downloaded.")

    frame0 = cv2.imread(first)
    h, w = frame0.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

    for idx, p in enumerate(img_paths):
        if not p or not os.path.exists(p):
            continue
        img = cv2.imread(p)
        if img is None:
            continue

        # Attribution / HUD
        overlay = img.copy()
        text1 = "Mapillary imagery \u00A9 contributors"
        text2 = "Demo route preview (Miryang \u2192 Dongdaegu)"
        cv2.rectangle(overlay, (0, h-48), (w, h), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.35, img, 0.65, 0, img)
        cv2.putText(img, text1, (12, h-22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1, cv2.LINE_AA)
        cv2.putText(img, text2, (12, h-5),  cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1, cv2.LINE_AA)

        # write frames; if slow index, duplicate frames to simulate slowdown
        repeat = 3 if idx in slow_indices else 1
        for _ in range(repeat):
            vw.write(img)

    vw.release()

def main():
    print("Fetching route from Kakao Directions API...")
    vertices, guides = get_route_vertices_and_guides(ORIGIN, DEST)
    print(f"Route points: {len(vertices)}, guides: {len(guides)}")

    print("Sampling route...")
    sampled = sample_along_path(vertices, step_m=SAMPLE_EVERY_M)
    print(f"Sampled points: {len(sampled)}")

    # Prepare slow-down indices around guide points
    slow_indices = set()
    for g in guides:
        gi = nearest_index(sampled, (g["lon"], g["lat"]))
        # around the point, mark a small neighborhood
        for d in range(-2, 3):
            if 0 <= gi+d < len(sampled):
                slow_indices.add(gi+d)

    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="mly_frames_"))
    print("Downloading Mapillary frames to:", tmpdir)

    img_paths = []
    for idx, (lon, lat) in enumerate(sampled):
        bbox = BBOX_START_DEG
        recvd = None
        # Try increasing bbox if nothing found
        while bbox <= BBOX_MAX_DEG and not recvd:
            recvd = mapillary_nearest_image(lon, lat, bbox, MAPILLARY_TOKEN)
            if not recvd:
                bbox *= 1.7
        if not recvd or not recvd.get("thumb_1024_url"):
            img_paths.append(None)
            continue

        url = recvd["thumb_1024_url"]
        outp = tmpdir / f"frame_{idx:04d}.jpg"
        ok = download_image(url, str(outp))
        img_paths.append(str(outp) if ok else None)

        if idx % 10 == 0:
            print(f"  {idx}/{len(sampled)} frames...")

    # Filter out leading None frames to ensure the first frame exists
    if all(p is None for p in img_paths):
        raise RuntimeError("No Mapillary images found along this route (coverage too sparse).")

    print("Building video...")
    build_video_from_images(img_paths, OUT_MP4, slow_indices=slow_indices, fps=VIDEO_FPS)
    print("Done ->", OUT_MP4)

    # Clean up temp frames
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass

if __name__ == "__main__":
    main()
