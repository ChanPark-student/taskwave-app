// src/main.tsx
import './index.css'
import App from './App.tsx'

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.tsx' // 1. AuthProvider 임포트


// 🔧 핫픽스: 컴포넌트 CSS를 강제로 포함
import './Header.css'
import './TaskwaveUpload.css'
import './FileExplorerPage.css'
import './LoginPage.css'
import './MyPage.css'
import './SignupPage.css'
import './AdditionalInfoPage.css'
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      {/* 2. App 컴포넌트를 AuthProvider로 감싸기 */}
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)