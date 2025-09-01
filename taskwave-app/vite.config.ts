import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  base: '/', // Render 배포시 정적 경로
  server: {
    proxy: {
      // 프론트에서 /api/* 로 호출하면 로컬 개발 중엔 백엔드로 프록시
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // pathRewrite가 필요하면 다음 줄 주석 해제 (현재 백엔드가 /api 프리픽스를 쓰므로 보통 불필요)
        // rewrite: (path) => path.replace(/^\/api/, '')
      },
    },
  },
})
