// taskwave-app/src/lib/http.ts
// API 베이스: .env 없으면 ''(빈 문자열) → '/api/...' 경로를 그대로 사용
export const API_BASE = import.meta.env.VITE_API_URL ?? '';

export function buildUrl(path: string) {
  if (path.startsWith('http')) return path;
  return path.startsWith('/') ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
}

// 토큰
export function saveToken(t: string) { localStorage.setItem('token', t); }
export function loadToken(): string | null { return localStorage.getItem('token'); }
export function clearToken() { localStorage.removeItem('token'); }

// Authorization 헤더
export function authHeaders(token?: string | null): HeadersInit {
  const t = token ?? loadToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export type FetchOptions = RequestInit & {
  /** JSON 바디를 넘기면 자동으로 stringify + 헤더 세팅 */
  json?: unknown;
  /** true면 JSON 파싱을 시도하지 않음(Text로 반환) */
  asText?: boolean;
  /** Authorization 헤더 생략이 필요할 때 */
  skipAuth?: boolean;
};

export async function fetchJSON<T = unknown>(path: string, opts: FetchOptions = {}): Promise<T> {
  const url = buildUrl(path);

  const { json, headers, asText, skipAuth, ...rest } = opts;

  // 헤더 구성
  const h = new Headers(headers || {});
  if (json !== undefined && !h.has('Content-Type')) {
    h.set('Content-Type', 'application/json');
  }
  if (!h.has('Accept')) h.set('Accept', 'application/json');

  // 토큰 자동 첨부
  if (!skipAuth) {
    const auth = authHeaders();
    Object.entries(auth).forEach(([k, v]) => h.set(k, String(v)));
  }

  // 바디 구성: json 옵션 우선 → 아니면 기존 body 검사
  let body = json !== undefined ? JSON.stringify(json) : (rest.body as BodyInit | undefined);

  // FormData이면 Content-Type 세팅을 제거(브라우저가 정함)
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  if (isFormData) h.delete('Content-Type');

  const res = await fetch(url, { ...rest, headers: h, body });

  // HTTP 에러 처리(본문이 text일 수도 있으므로 먼저 text로 읽어 메시지 구성)
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(errText || `HTTP ${res.status} ${res.statusText}`);
  }

  // text 그대로 원하면
  if (asText) {
    return (await res.text()) as T;
  }

  // 204 No Content → undefined 반환
  if (res.status === 204) {
    return undefined as T;
  }

  // JSON 응답 여부 확인
  const ctype = res.headers.get('content-type') || '';

  // 본문을 text로 읽고, 비어있으면 undefined
  const text = await res.text().catch(() => '');
  if (!text) {
    return undefined as T;
  }

  // content-type이 JSON이 아니면 파싱 시도하지 않음
  if (!ctype.includes('application/json')) {
    return undefined as T;
  }

  // 안전 파싱
  try {
    return JSON.parse(text) as T;
  } catch {
    // JSON 깨진 경우도 안전하게 undefined 반환
    return undefined as T;
  }
}
