import { Routes, Route } from 'react-router-dom'
import TaskwaveUpload from './TaskwaveUpload.js' 
import SignupPage from './SignupPage.js'
import LoginPage from './LoginPage.js'
import MyPage from './MyPage.js'
import FileExplorerPage from './FileExplorerPage.js'
import AdditionalInfoPage from './AdditionalInfoPage.js'; // 1. 새 페이지 임포트

function App() {
  return (
    <Routes>
      <Route path="/" element={<TaskwaveUpload />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/mypage" element={<MyPage />} />
      
      <Route path="/files" element={<FileExplorerPage />} />
      <Route path="/files/:subject" element={<FileExplorerPage />} />
      <Route path="/files/:subject/:week" element={<FileExplorerPage />} />
      <Route path="/files/:subject/:week/:day" element={<FileExplorerPage />} />

      {/* 2. 추가 정보 페이지 경로 추가 */}
      <Route path="/signup-info" element={<AdditionalInfoPage />} />
    </Routes>
  )
}

export default App