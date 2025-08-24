// api.ts (전체 교체)

// API BASE
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://localhost:8000/api";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// 공통: 토큰 헬퍼
const tokenKey = "token";
const getToken = () => (typeof window !== "undefined" ? localStorage.getItem(tokenKey) : null);
const setToken = (t: string) => typeof window !== "undefined" && localStorage.setItem(tokenKey, t);
const clearToken = () => typeof window !== "undefined" && localStorage.removeItem(tokenKey);

// 공통: 에러 메시지 파서(FastAPI의 detail 형태 대응)
function parseErrorMessage(data: any, fallback = "Request failed") {
  try {
    if (!data) return fallback;
    if (typeof data === "string") return data;
    if (data.detail) {
      const d = data.detail;
      if (typeof d === "string") return d;
      const arr = Array.isArray(d) ? d : [d];
      const msgs = arr
        .map((e: any) => e?.msg || e?.type || (typeof e === "string" ? e : ""))
        .filter(Boolean);
      return msgs.join(", ") || fallback;
    }
    if (data.message) return data.message;
    return JSON.stringify(data);
  } catch {
    return fallback;
  }
}

// 공통: JSON fetch 래퍼
async function fetchJSON<T>(
  path: string,
  init: RequestInit = {},
  useAuth = false
): Promise<ApiResponse<T>> {
  try {
    const headers: Record<string, string> = {
      ...(init.headers as Record<string, string> | undefined),
    };

    if (init.body && !(init.body instanceof FormData)) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
    }
    if (useAuth) {
      const t = getToken();
      if (t) headers["Authorization"] = `Bearer ${t}`;
    }

    const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
    const data = await res
      .json()
      .catch(() => ({})); // JSON 아닐 경우 대비

    if (!res.ok) {
      return { error: parseErrorMessage(data, `${res.status} ${res.statusText}`) };
    }
    return { data };
  } catch {
    return { error: "Network error" };
  }
}

// ================== 인증 ==================
export const authApi = {
  login: async (
    email: string,
    password: string
  ): Promise<ApiResponse<{ access_token: string; user: any }>> => {
    // 1) 로그인 → 토큰 저장
    const loginRes = await fetchJSON<{ access_token: string; token_type: string }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
      false
    );
    if (loginRes.error || !loginRes.data) return { error: loginRes.error };

    setToken(loginRes.data.access_token);

    // 2) 내 정보 가져오기
    const meRes = await fetchJSON<any>("/users/me", { method: "GET" }, true);
    if (meRes.error) {
      // 프로필 로딩 실패해도 토큰은 유효 — 필요시 토큰 유지
      return { data: { access_token: loginRes.data.access_token, user: null } };
    }
    return { data: { access_token: loginRes.data.access_token, user: meRes.data } };
  },

  register: async (email: string, password: string): Promise<ApiResponse<{ access_token: string }>> => {
    // name 없이 보내도 백엔드가 허용되게 바꿨다면 그대로 사용 가능.
    // 백엔드가 아직 name 필수면 아래 one-liner로 자동 생성:
    const body = { email, password, name: email.split("@")[0] };

    const res = await fetchJSON<{ access_token: string; token_type: string }>(
      "/auth/signup",
      { method: "POST", body: JSON.stringify(body) },
      false
    );
    if (res.error || !res.data) return { error: res.error };
    // 토큰 저장(선택)
    setToken(res.data.access_token);
    return { data: { access_token: res.data.access_token } };
  },

  logout: () => {
    clearToken();
  },
};

// ================== 사용자 ==================
export const userApi = {
  getProfile: async (): Promise<ApiResponse<any>> => {
    return fetchJSON<any>("/users/me", { method: "GET" }, true);
  },

  updateProfile: async (profileData: any): Promise<ApiResponse<any>> => {
    return fetchJSON<any>(
      "/users/me",
      {
        method: "PUT",
        body: JSON.stringify(profileData),
      },
      true
    );
  },
};

// ================== 과목 ==================
export const subjectApi = {
  getSubjects: async (): Promise<ApiResponse<any[]>> => {
    return fetchJSON<any[]>("/subjects", { method: "GET" }, true);
  },
  // 필요 시 과목 생성/삭제도 쉽게 확장 가능:
  // create: (title: string) => fetchJSON<any>("/subjects", { method:"POST", body: JSON.stringify({title}) }, true),
};

// ================== 시간표 ==================
export const scheduleApi = {
  getSchedule: async (): Promise<ApiResponse<any>> => {
    return fetchJSON<any>("/timetable", { method: "GET" }, true);
  },

  uploadSchedule: async (file: File): Promise<ApiResponse<any>> => {
    const formData = new FormData();
    formData.append("file", file);
    // FormData 전송 시 Content-Type 헤더 넣지 말 것(브라우저가 boundary 자동 설정)
    try {
      const t = getToken();
      const res = await fetch(`${API_BASE_URL}/timetable/upload`, {
        method: "POST",
        headers: t ? { Authorization: `Bearer ${t}` } : undefined,
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return { error: parseErrorMessage(data) };
      return { data };
    } catch {
      return { error: "Network error" };
    }
  },
};

// ================== 학습 자료 ==================
export const materialApi = {
  getMaterials: async (opts?: {
    subjectId?: string;
    week?: string;
    day?: string;
  }): Promise<ApiResponse<any[]>> => {
    const params = new URLSearchParams();
    if (opts?.subjectId) params.set("subject_id", opts.subjectId);
    if (opts?.week) params.set("week", opts.week);
    if (opts?.day) params.set("day", opts.day);

    const q = params.toString();
    const path = q ? `/materials?${q}` : "/materials";
    return fetchJSON<any[]>(path, { method: "GET" }, true);
  },

  // 필요 시 단건 업로드도 여기에 둘 수 있음.
};

// ================== 파일 업로드(자료 업로드에 맞춤) ==================
export const uploadApi = {
  // 백엔드 스펙: POST /materials/upload
  // FormData fields: file, subject_id (필수), name(선택), week(선택), day(선택)
  uploadFile: async (
    file: File,
    metadata: { subject_id: string; name?: string; week?: string; day?: string }
  ): Promise<ApiResponse<any>> => {
    try {
      const t = getToken();
      const formData = new FormData();
      formData.append("file", file);
      formData.append("subject_id", metadata.subject_id);
      if (metadata.name) formData.append("name", metadata.name);
      if (metadata.week) formData.append("week", metadata.week);
      if (metadata.day) formData.append("day", metadata.day);

      const res = await fetch(`${API_BASE_URL}/materials/upload`, {
        method: "POST",
        headers: t ? { Authorization: `Bearer ${t}` } : undefined,
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return { error: parseErrorMessage(data) };
      return { data };
    } catch {
      return { error: "Network error" };
    }
  },
};

// === 추가: 시간표 업로드/파싱 전용 ===
export const timetableApi = {
  upload: async (file: File): Promise<ApiResponse<{ id: string } & any>> => {
    try {
      const token = localStorage.getItem("token")
      const form = new FormData()
      form.append("file", file)

      const res = await fetch(`${API_BASE_URL}/timetable/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: form, // Content-Type 지정하지 말 것!
      })
      const data = await res.json().catch(() => ({}))
      return res.ok ? { data } : { error: parseErrorMessage(data) }
    } catch {
      return { error: "Network error" }
    }
  },

  list: async (): Promise<ApiResponse<any[]>> => {
    try {
      const token = localStorage.getItem("token")
      const res = await fetch(`${API_BASE_URL}/timetable/uploads`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      })
      const data = await res.json().catch(() => ({}))
      return res.ok ? { data } : { error: parseErrorMessage(data) }
    } catch {
      return { error: "Network error" }
    }
  },

  parse: async (uploadId: string): Promise<ApiResponse<any>> => {
    try {
      const token = localStorage.getItem("token")
      const res = await fetch(`${API_BASE_URL}/timetable/${uploadId}/parse`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      })
      const data = await res.json().catch(() => ({}))
      return res.ok ? { data } : { error: parseErrorMessage(data) }
    } catch {
      return { error: "Network error" }
    }
  },
}
