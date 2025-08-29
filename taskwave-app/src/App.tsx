import { Routes, Route } from 'react-router-dom'
import TaskwaveUpload from './TaskwaveUpload.js' 
import SignupPage from './SignupPage.js'
import LoginPage from './LoginPage.js'
import MyPage from './MyPage.js'
import FileExplorerPage from './FileExplorerPage.js'
import AdditionalInfoPage from './AdditionalInfoPage.js';
import ManualSchedulePage from './ManualSchedulePage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<TaskwaveUpload />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/mypage" element={<MyPage />} />
      
      {/* 파일 탐색기 라우팅을 새로운 구조로 수정 */}
      <Route path="/files" element={<FileExplorerPage />} />
      <Route path="/files/:subject" element={<FileExplorerPage />} />
      <Route path="/files/:subject/:date" element={<FileExplorerPage />} />

      {/* 2. 추가 정보 페이지 경로 추가 */}
      <Route path="/signup-info" element={<AdditionalInfoPage />} />

      {/* 3. 시간표 수동 입력 페이지 경로 추가 */}
      <Route path="/add-schedule" element={<ManualSchedulePage />} />
    </Routes>
  )
}

export default App