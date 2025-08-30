export const EP = {
  AUTH_LOGIN: '/api/auth/login',
  AUTH_SIGNUP: '/api/auth/signup',

  ME: '/api/users/me',

  // 파일/폴더 구조
  FILES_STRUCTURE: '/api/files/structure',

  // 주간 시간표 뷰
  SCHEDULES_WEEK_VIEW: '/api/schedules/week-view',

  SUBJECTS: '/api/subjects',
  SUBJECT: (id: number|string) => `/api/subjects/${id}`,
  SUBJECT_WEEKS: (id: number|string) => `/api/subjects/${id}/weeks`,
  WEEK_SESSIONS: (id: number|string) => `/api/weeks/${id}/sessions`,

  MATERIALS_UPLOAD: '/api/materials/upload',
  SUBJECT_MATERIALS: (sid: number|string) => `/api/subjects/${sid}/materials`,
  MATERIAL: (mid: number|string) => `/api/materials/${mid}`,

  TIMETABLE_UPLOAD: '/api/timetable/upload',
  UPLOADS_AUTO_SORT: '/api/uploads/auto-sort', // 자동 분류 업로드
  SCHEDULES_MANUAL: '/api/schedules/manual',
  SCHEDULES_RECURRING: '/api/schedules/recurring', // 반복 일정 생성

  SCHEDULES_PING: '/api/schedules/ping',
  HEALTH: '/api/health',
} as const
