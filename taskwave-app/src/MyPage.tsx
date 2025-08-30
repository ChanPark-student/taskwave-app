import { useState, useEffect, useCallback, ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUploadCloud } from 'react-icons/fi';
import Header from './Header.tsx';
import { useAuth, User } from './context/AuthContext.tsx';
import { fetchJSON } from './lib/http';
import { EP } from './lib/endpoints';
import './MyPage.css';

// API 응답 데이터 타입 정의
interface Session {
  subject_title: string;
  session_id: string;
  day_of_week: string;
  start_time: string; // "HH:MM:SS"
  end_time: string;   // "HH:MM:SS"
  color: string | null;
}

// 주간 시간표 뷰 컴포넌트
const WeeklyTimetableView = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState(1); // 기본 1주차

  const fetchSessions = useCallback(async (week: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const url = `${EP.SCHEDULES_WEEK_VIEW}?week_no=${week}`;
      const data = await fetchJSON<Session[]>(url, { method: 'GET' });
      setSessions(data);
    } catch (err) {
      setError('시간표 정보를 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions(selectedWeek);
  }, [selectedWeek, fetchSessions]);

  const timeToRow = (time: string): number => {
    const [hour, minute] = time.split(':').map(Number);
    return (hour - 9) * 2 + (minute / 30) + 2;
  };

  const dayToColumn = (day: string): number => {
    const dayMap: { [key: string]: number } = { '월': 2, '화': 3, '수': 4, '목': 5, '금': 6, '토': 7, '일': 8 };
    return dayMap[day] || -1;
  };

  const timeLabels = Array.from({ length: (20 - 9) * 2 }, (_, i) => {
    const hour = 9 + Math.floor(i / 2);
    const minute = (i % 2) * 30;
    return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
  });

  // HH:MM:SS -> HH:MM 형식으로 바꾸는 헬퍼 함수
  const formatTime = (timeStr?: string) => timeStr?.substring(0, 5) || '';

  return (
    <section className="timetable-view-section">
      <div className="section-header">
        <h2>주간 시간표</h2>
        <div className="week-selector">
          <button onClick={() => setSelectedWeek(w => Math.max(1, w - 1))} disabled={selectedWeek === 1}>&lt; 이전 주</button>
          <span>{selectedWeek}주차</span>
          <button onClick={() => setSelectedWeek(w => w + 1)}>다음 주 &gt;</button>
        </div>
      </div>
      <div className="timetable-grid-container">
        {isLoading && <div className="grid-overlay">로딩 중...</div>}
        {error && <div className="grid-overlay error">{error}</div>}
        {!isLoading && !error && sessions.length === 0 && <div className="grid-overlay">해당 주차에 강의가 없습니다.</div>}
        
        <div className="timetable-grid">
          <div className="grid-header">시간</div>
          {["월", "화", "수", "목", "금", "토", "일"].map(day => <div key={day} className="grid-header">{day}</div>)}

          {timeLabels.map(label => (
            <div key={label} className="time-label-cell">{label}</div>
          ))}

          {sessions.map(session => {
            const gridColumn = dayToColumn(session.day_of_week);
            const gridRowStart = timeToRow(session.start_time);
            const gridRowEnd = timeToRow(session.end_time);
            const startTimeFormatted = formatTime(session.start_time);
            const endTimeFormatted = formatTime(session.end_time);

            if (gridColumn === -1 || gridRowStart < 2) return null;

            return (
              <div
                key={session.session_id}
                className="session-block"
                style={{
                  gridColumn: gridColumn,
                  gridRow: `${gridRowStart} / ${gridRowEnd}`,
                  backgroundColor: session.color || '#4A90E2',
                }}
                title={`${session.subject_title} (${startTimeFormatted}-${endTimeFormatted})`}
              >
                <div className="session-title">{session.subject_title}</div>
                <div className="session-time">{startTimeFormatted} - {endTimeFormatted}</div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

const MyPage = () => {
  const navigate = useNavigate();
  const { user, updateProfile } = useAuth();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [tempProfile, setTempProfile] = useState<User | null>(user);
  const [timetableImage, setTimetableImage] = useState<string | null>(null);

  useEffect(() => {
    setTempProfile(user);
  }, [user]);

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setTimetableImage(URL.createObjectURL(file));
    }
  };

  const handleEditClick = () => {
    setTempProfile(user);
    setIsEditingProfile(true);
  };

  const handleSaveClick = () => {
    if (tempProfile) {
      updateProfile(tempProfile);
    }
    setIsEditingProfile(false);
  };

  const handleCancelClick = () => {
    setIsEditingProfile(false);
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTempProfile(prevProfile => prevProfile ? { ...prevProfile, [name]: value } : null);
  };

  if (!user) {
    return <div>로딩 중...</div>;
  }

  return (
    <div className="page-container">
      <Header />
      <main className="mypage-main-content">
        <h1 className="mypage-title">내 계정</h1>
        <div className="mypage-layout">
          <section className="profile-section">
            <div className="section-header">
              <h2>프로필</h2>
              {!isEditingProfile ? (
                <button onClick={handleEditClick} className="change-button">변경</button>
              ) : (
                <div className="edit-actions">
                  <button onClick={handleSaveClick} className="save-button">저장</button>
                  <button onClick={handleCancelClick} className="cancel-button">취소</button>
                </div>
              )}
            </div>
            {!isEditingProfile ? (
              <div className="profile-details">
                <p><strong>성명</strong><span>{user.name || '-'}</span></p>
                <p><strong>학교</strong><span>{user.school || '-'}</span></p>
                <p><strong>생년월일</strong><span>{user.birth || '-'}</span></p>
              </div>
            ) : (
              <div className="profile-edit-form">
                <div className="form-row">
                  <label htmlFor="name">성명</label>
                  <input type="text" id="name" name="name" value={tempProfile?.name || ''} onChange={handleInputChange} />
                </div>
                <div className="form-row">
                  <label htmlFor="school">학교</label>
                  <input type="text" id="school" name="school" value={tempProfile?.school || ''} onChange={handleInputChange} />
                </div>
                <div className="form-row">
                  <label htmlFor="birth">생년월일</label>
                  <input type="text" id="birth" name="birth" value={tempProfile?.birth || ''} onChange={handleInputChange} />
                </div>
              </div>
            )}
          </section>

          <div className="timetable-management-area">
            <WeeklyTimetableView />
            <section className="timetable-upload-section">
              <div className="section-header">
                <h2>시간표 관리</h2>
              </div>
              {!timetableImage ? (
                <div className="timetable-upload-box">
                  <div className="upload-area">
                    <FiUploadCloud className="upload-icon" />
                    <p>시간표 파일을 업로드하면 자동으로 분석해 드립니다.</p>
                    <label htmlFor="timetable-upload" className="upload-button">파일 업로드</label>
                    <input id="timetable-upload" type="file" accept="image/*,.pdf" onChange={handleImageUpload} style={{ display: 'none' }} />
                  </div>
                </div>
              ) : (
                <div className="timetable-display-box">
                  <p>현재 업로드된 시간표:</p>
                  <img src={timetableImage} alt="업로드된 시간표" />
                  <label htmlFor="timetable-modify" className="change-button">다른 파일 선택</label>
                  <input id="timetable-modify" type="file" accept="image/*,.pdf" onChange={handleImageUpload} style={{ display: 'none' }} />
                </div>
              )}
              <button onClick={() => navigate('/add-schedule')} className="manual-add-button">수동으로 시간표 입력</button>
            </section>
          </div>

        </div>
      </main>
    </div>
  );
};

export default MyPage;
