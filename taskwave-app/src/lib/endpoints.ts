// 최종 수정: Gemini (2025-08-31)

export const EP = {
  AUTH_LOGIN: '/api/auth/login',
  AUTH_SIGNUP: '/api/auth/signup',

  ME: '/api/users/me',

  // 파일/폴더 구조
  FILES_STRUCTURE: '/api/files/structure',

  // 주간 시간표 뷰
  SCHEDULES_WEEK_VIEW: '/api/schedules/week-view',

  // 과목
  SUBJECTS: '/api/subjects',
  SUBJECT: (id: number|string) => `/api/subjects/${id}`,
  SUBJECT_DELETE: (id: number|string) => `/api/subjects/${id}`,
  
  // 주차
  SUBJECT_WEEKS: (id: number|string) => `/api/subjects/${id}/weeks`,
  WEEK_SESSIONS: (id: number|string) => `/api/weeks/${id}/sessions`,

  // 자료
  MATERIALS_UPLOAD: '/api/materials/upload',
  SUBJECT_MATERIALS: (sid: number|string) => `/api/subjects/${sid}/materials`,
  MATERIAL: (mid: number|string) => `/api/materials/${mid}`,

  // 업로드
  TIMETABLE_UPLOAD: '/api/timetable/upload',
  UPLOADS_AUTO_SORT: '/api/uploads/auto-sort',

  // 스케줄 생성
  SCHEDULES_MANUAL: '/api/schedules/manual',
  SCHEDULES_RECURRING: '/api/schedules/recurring',

  // 헬스체크
  SCHEDULES_PING: '/api/schedules/ping',
  HEALTH: '/api/health',
} as const;