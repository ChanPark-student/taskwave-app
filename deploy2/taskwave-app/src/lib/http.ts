// src/lib/http.ts
// 기본값을 ''(빈 문자열)로 바꿔서 EP가 '/api/...'여도 이중 프리픽스가 안 생기게 함.
export const API_BASE = import.meta.env.VITE_API_URL ?? '';

export function buildUrl(path: string) {
  if (path.startsWith('http')) return path;
  // path가 '/api/...'처럼 절대경로면 그냥 이어붙임 (API_BASE가 ''이면 그대로 '/api/...')
  return path.startsWith('/') ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
}

// 토큰 키 통일: 'token'
export function saveToken(t: string) { localStorage.setItem('token', t); }
export function loadToken(): string | null { return localStorage.getItem('token'); }
export function clearToken() { localStorage.removeItem('token'); }

// Authorization 헤더 생성
export function authHeaders(token?: string | null): HeadersInit {
  const t = token ?? loadToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function fetchJSON<T>(
  path: string,
  init: RequestInit = {},
  autoJson = true
): Promise<T> {
  const url = buildUrl(path);

  // 객체 바디면 자동으로 JSON.stringify, FormData면 그대로
  let body: BodyInit | undefined = init.body as any;
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  if (body !== undefined && !isFormData && typeof body !== 'string') {
    body = JSON.stringify(body);
  }

  const headers: HeadersInit = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    // ★ 토큰 자동 첨부 (로그인/회원가입처럼 토큰이 없으면 빈 헤더라 문제 없음)
    ...authHeaders(),
    ...(init.headers || {}),
  };

  const res = await fetch(url, { ...init, headers, body });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `HTTP ${res.status}`);
  }

  if (!autoJson) {
    const text = await res.text();
    return text as unknown as T;
  }
  // 204 No Content 대응
  if (res.status === 204) return undefined as T;

  return (await res.json()) as T;
}
