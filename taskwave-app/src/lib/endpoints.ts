export const EP = {
  AUTH_LOGIN: '/api/auth/login',
  AUTH_SIGNUP: '/api/auth/signup',

  ME: '/api/users/me',

  SUBJECTS: '/api/subjects',
  SUBJECT: (id: number|string) => `/api/subjects/${id}`,
  SUBJECT_WEEKS: (id: number|string) => `/api/subjects/${id}/weeks`,
  WEEK_SESSIONS: (id: number|string) => `/api/weeks/${id}/sessions`,

  MATERIALS_UPLOAD: '/api/materials/upload',
  SUBJECT_MATERIALS: (sid: number|string) => `/api/subjects/${sid}/materials`,
  MATERIAL: (mid: number|string) => `/api/materials/${mid}`,

  TIMETABLE_UPLOAD: '/api/timetable/upload',
  SCHEDULES_MANUAL: '/api/schedules/manual',

  SCHEDULES_PING: '/api/schedules/ping',
  HEALTH: '/api/health',
} as const
