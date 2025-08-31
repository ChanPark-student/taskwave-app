import { Routes, Route } from 'react-router-dom'
import TaskwaveUpload from './TaskwaveUpload.tsx' 
import SignupPage from './SignupPage.tsx'
import LoginPage from './LoginPage.tsx'
import MyPage from './MyPage.tsx'
import FileExplorerPage from './FileExplorerPage.tsx'
import AdditionalInfoPage from './AdditionalInfoPage.tsx';
import ManualSchedulePage from './ManualSchedulePage';
import SubjectEventsPage from './SubjectEventsPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<TaskwaveUpload />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/mypage" element={<MyPage />} />
      
      {/* 파일 탐색기 및 이벤트 라우팅 */}
      <Route path="/files" element={<FileExplorerPage />} />
      <Route path="/files/:subject" element={<FileExplorerPage />} />
      <Route path="/files/:subject/events" element={<SubjectEventsPage />} />

      {/* 추가 정보 페이지 경로 */}
      <Route path="/signup-info" element={<AdditionalInfoPage />} />

      {/* 시간표 수동 입력 페이지 경로 */}
      <Route path="/add-schedule" element={<ManualSchedulePage />} />
    </Routes>
  )
}

export default App