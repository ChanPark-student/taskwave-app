import { useState, useEffect, useCallback, ChangeEvent, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUploadCloud, FiPlusCircle, FiChevronUp, FiChevronDown } from 'react-icons/fi';
import Header from './Header.tsx';
import { useAuth, User } from './context/AuthContext.tsx';
import { fetchJSON } from './lib/http';
import { EP } from './lib/endpoints';
import './MyPage.css';

// --- 타입 정의 ---
interface Session {
  subject_title: string;
  session_id: string;
  day_of_week: string;
  start_time: string;
  end_time: string;
  color: string | null;
}

interface RecurringSchedulePayload {
  title: string;
  start_date: string;
  end_date: string;
  start_time: string;
  end_time: string;
  weekdays: string[];
}

// --- 자식 컴포넌트 ---

const WeeklyTimetableView = () => {
  // ... (기존 WeeklyTimetableView 코드는 변경 없음, 생략) ...
};

const RecurringScheduleForm = ({ onSave }: { onSave: () => void }) => {
  const [title, setTitle] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [weekdays, setWeekdays] = useState<Record<string, boolean>>({
    '월': false, '화': false, '수': false, '목': false, '금': false, '토': false, '일': false,
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleWeekdayChange = (day: string) => {
    setWeekdays(prev => ({ ...prev, [day]: !prev[day] }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const selectedDays = Object.keys(weekdays).filter(day => weekdays[day]);
    if (!title || !startDate || !endDate || !startTime || !endTime || selectedDays.length === 0) {
      setError('모든 필드를 올바르게 입력해주세요.');
      return;
    }

    const payload: RecurringSchedulePayload = {
      title,
      start_date: startDate,
      end_date: endDate,
      start_time: startTime,
      end_time: endTime,
      weekdays: selectedDays,
    };

    setIsSubmitting(true);
    try {
      await fetchJSON(EP.SCHEDULES_RECURRING, { 
        method: 'POST', 
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' }
      });
      onSave(); // 부모 컴포넌트에 저장 완료 알림
    } catch (err: any) {
      setError(err?.detail || '일정 생성에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="recurring-form">
      <div className="form-grid">
        <div className="form-row full-width">
          <label htmlFor="title">일정 이름</label>
          <input id="title" type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="예: 알고리즘 스터디" />
        </div>
        <div className="form-row">
          <label htmlFor="start_date">시작 날짜</label>
          <input id="start_date" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
        </div>
        <div className="form-row">
          <label htmlFor="end_date">종료 날짜</label>
          <input id="end_date" type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
        </div>
        <div className="form-row">
          <label htmlFor="start_time">시작 시간</label>
          <input id="start_time" type="time" value={startTime} onChange={e => setStartTime(e.target.value)} />
        </div>
        <div className="form-row">
          <label htmlFor="end_time">종료 시간</label>
          <input id="end_time" type="time" value={endTime} onChange={e => setEndTime(e.target.value)} />
        </div>
        <div className="form-row full-width weekday-selector">
          <label>반복 요일</label>
          <div className="weekdays">
            {Object.keys(weekdays).map(day => (
              <button 
                type="button"
                key={day} 
                className={`weekday-btn ${weekdays[day] ? 'selected' : ''}`}
                onClick={() => handleWeekdayChange(day)}
              >
                {day}
              </button>
            ))}
          </div>
        </div>
      </div>
      {error && <p className="form-error">{error}</p>}
      <button type="submit" className="save-button" disabled={isSubmitting}>
        {isSubmitting ? '저장 중...' : '반복 일정 저장'}
      </button>
    </form>
  );
};

// --- 메인 페이지 컴포넌트 ---
const MyPage = () => {
  const navigate = useNavigate();
  const { user, updateProfile, refreshMe } = useAuth();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [tempProfile, setTempProfile] = useState<User | null>(user);
  const [timetableImage, setTimetableImage] = useState<string | null>(null);
  const [showRecurringForm, setShowRecurringForm] = useState(false);

  useEffect(() => {
    setTempProfile(user);
  }, [user]);

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setTimetableImage(URL.createObjectURL(file));
  };

  const handleEditClick = () => {
    setTempProfile(user);
    setIsEditingProfile(true);
  };

  const handleSaveClick = () => {
    if (tempProfile) updateProfile(tempProfile);
    setIsEditingProfile(false);
  };

  const handleCancelClick = () => setIsEditingProfile(false);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTempProfile(prev => (prev ? { ...prev, [name]: value } : null));
  };

  const handleRecurringSave = async () => {
    setShowRecurringForm(false);
    await refreshMe(); // 데이터 새로고침
  };

  if (!user) return <div>로딩 중...</div>;

  return (
    <div className="page-container">
      <Header />
      <main className="mypage-main-content">
        <h1 className="mypage-title">내 계정</h1>
        <div className="mypage-layout">
          <section className="profile-section">
            {/* ... 프로필 UI ... */}
          </section>

          <div className="timetable-management-area">
            <WeeklyTimetableView />

            {/* 새로운 개인 일정 관리 섹션 */}
            <section className="personal-schedule-section">
              <div className="section-header" onClick={() => setShowRecurringForm(p => !p)} style={{cursor: 'pointer'}}>
                <h2>개인 일정 추가</h2>
                <button className="toggle-button">
                  {showRecurringForm ? <FiChevronUp /> : <FiChevronDown />}
                </button>
              </div>
              {showRecurringForm && <RecurringScheduleForm onSave={handleRecurringSave} />}
            </section>

            {/* 기존 시간표 관리 섹션 */}
            <section className="timetable-upload-section">
              {/* ... 기존 업로드/수동입력 UI ... */}
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default MyPage;
