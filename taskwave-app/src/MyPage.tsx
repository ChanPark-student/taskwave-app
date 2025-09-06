import { useState, useEffect, useCallback, ChangeEvent, FormEvent, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUploadCloud, FiChevronUp, FiChevronDown, FiTrash2 } from 'react-icons/fi';
import Header from './Header.tsx';
import { useAuth, User } from './context/AuthContext.tsx'; // FileSystemStructure 임포트 제거
import { fetchJSON } from './lib/http';
import { EP } from './lib/endpoints';
import './MyPage.css';
import './ManualSchedulePage.css';

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

interface ScheduleSlot {
  id: number;
  subject_title: string;
  weekday: string;
  start_time: string;
  end_time: string;
}

const ManualScheduleForm = ({ onSave }: { onSave: () => void }) => {
  const [url, setUrl] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const [slots, setSlots] = useState<ScheduleSlot[]>([
    { id: 1, subject_title: '', weekday: '월', start_time: '09:00', end_time: '10:30' },
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const clearMessages = () => {
    setError(null);
    setSuccessMessage(null);
  };

  const handleAddSlot = () => setSlots([...slots, { ...slots[0], id: Date.now() }]);
  const handleSlotChange = (id: number, field: keyof ScheduleSlot, value: string) => {
    setSlots(slots.map(slot => (slot.id === id ? { ...slot, [field]: value } : slot)));
  };
  const handleRemoveSlot = (id: number) => setSlots(slots.filter(slot => slot.id !== id));

  const handleUrlSubmit = async () => {
    if (!url || !startDate || !endDate) {
      setError('URL, 시작일, 종료일을 모두 입력해주세요.');
      return;
    }
    setLoading(true);
    clearMessages();
    try {
      const response = await fetchJSON<{ status: string; message: string }>(EP.SCHEDULES_SCRAPE_AND_GENERATE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, start_date: startDate, end_date: endDate })
      });
      setSuccessMessage(response.message || 'URL에서 시간표를 성공적으로 가져왔습니다!');
      setTimeout(() => onSave(), 2000);
    } catch (err: any) {
      setError(err.message || 'URL에서 시간표를 가져오는 데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async () => {
    if (!slots.some(s => s.subject_title)) {
      setError('최소 하나 이상의 강의를 입력해주세요.');
      return;
    }
    setLoading(true);
    clearMessages();
    try {
      await fetchJSON(EP.SCHEDULES_MANUAL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slots })
      });
      setSuccessMessage('시간표가 성공적으로 저장되었습니다!');
      setTimeout(() => onSave(), 2000);
    } catch (err: any) {
      setError(err?.message ?? '저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="manual-schedule-container">
      <div className="import-section url-import-section">
        <h3>URL에서 가져오기</h3>
        <div className="form-group">
          <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="시간표 페이지 URL (예: 에브리타임)" />
        </div>
        <div className="form-group-row">
          <div className="form-group">
            <label>학기 시작일</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>학기 종료일</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
        </div>
        <div className="form-actions">
          <button onClick={handleUrlSubmit} className="save-btn" disabled={loading}>{loading ? '저장 중...' : 'URL로 시간표 저장'}</button>
        </div>
      </div>

      <div className="divider-or">또는</div>

      <div className="import-section manual-add-section">
        <h3>수동으로 입력하기</h3>
        <div className="schedule-form-container">
          {slots.map((slot) => (
            <div key={slot.id} className="slot-row">
              <input type="text" placeholder="과목명" value={slot.subject_title} onChange={e => handleSlotChange(slot.id, 'subject_title', e.target.value)} />
              <select value={slot.weekday} onChange={e => handleSlotChange(slot.id, 'weekday', e.target.value)}>
                {['월', '화', '수', '목', '금', '토', '일'].map(day => <option key={day} value={day}>{day}</option>)}
              </select>
              <input type="time" value={slot.start_time} onChange={e => handleSlotChange(slot.id, 'start_time', e.target.value)} />
              <span>~</span>
              <input type="time" value={slot.end_time} onChange={e => handleSlotChange(slot.id, 'end_time', e.target.value)} />
              {slots.length > 1 && <button onClick={() => handleRemoveSlot(slot.id)} className="remove-btn">-</button>}
            </div>
          ))}
          <div className="form-actions manual-actions">
            <button onClick={handleAddSlot} className="add-btn">+ 강의 추가</button>
            <button onClick={handleManualSubmit} className="save-btn" disabled={loading}>{loading ? '저장 중...' : '수동 입력 내용 저장'}</button>
          </div>
        </div>
      </div>
      
      <div className="message-area">
        {error && <p className="error-message">{error}</p>}
        {successMessage && <p className="success-message">{successMessage}</p>}
      </div>
    </div>
  );
};

const WeeklyTimetableView = () => {
  const { fileSystem } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState(1);

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

  const subjectColorMap = useMemo(() => {
    const PALETTE = ['#2979FF', '#00BFA5', '#651FFF', '#D50000', '#FF6D00', '#546E7A', '#C51162', '#0097A7', '#2E7D32', '#3D5AFE', '#D500F9', '#6D4C41'];
    const allSubjects = Object.keys(fileSystem).sort();
    const colorMap: Record<string, string> = {};
    allSubjects.forEach((subject, index) => {
      colorMap[subject] = PALETTE[index % PALETTE.length];
    });
    return colorMap;
  }, [fileSystem]);

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
          {timeLabels.map(label => <div key={label} className="time-label-cell">{label}</div>)}
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
                  backgroundColor: subjectColorMap[session.subject_title] || '#37474F',
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
      onSave();
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

const ScheduleListManager = () => {
  const { fileSystem, refreshMe } = useAuth();
  const [isDeleting, setIsDeleting] = useState<string | null>(null); 

  const handleDelete = async (subjectName: string, subjectId: string) => {
    if (window.confirm(`정말로 '${subjectName}' 일정을 삭제하시겠습니까?
이 작업은 되돌릴 수 없습니다.`)) {
      setIsDeleting(subjectId);
      try {
        await fetchJSON(EP.SUBJECT_DELETE(subjectId), { method: 'DELETE' });
        await refreshMe(); 
      } catch (error) {
        alert('삭제에 실패했습니다.');
        console.error(error);
      } finally {
        setIsDeleting(null);
      }
    }
  };

  const subjects = Object.entries(fileSystem);

  return (
    <section className="schedule-list-section">
      <div className="section-header">
        <h2>일정 목록 및 관리</h2>
      </div>
      <ul className="schedule-list">
        {subjects.length === 0 && <li className="empty-list">등록된 일정이 없습니다.</li>}
        {subjects.map(([name, data]) => (
          <li key={data.subject_id}>
            <span>{name}</span>
            <button 
              onClick={() => handleDelete(name, data.subject_id)} 
              disabled={isDeleting === data.subject_id}
              className="delete-button"
            >
              {isDeleting === data.subject_id ? '삭제 중...' : <FiTrash2 />}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
};


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
    await refreshMe();
  };

  if (!user) return <div>로딩 중...</div>;

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

            <section className="personal-schedule-section">
              <div className="section-header" onClick={() => setShowRecurringForm(p => !p)} style={{cursor: 'pointer'}}>
                <h2>개인 일정 추가</h2>
                <button className="toggle-button">
                  {showRecurringForm ? <FiChevronUp /> : <FiChevronDown />}
                </button>
              </div>
              {showRecurringForm && <RecurringScheduleForm onSave={handleRecurringSave} />}
            </section>

            <ScheduleListManager />

            <section className="timetable-input-section">
              <div className="section-header">
                <h2>시간표 입력</h2>
              </div>
              <ManualScheduleForm onSave={handleRecurringSave} />
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default MyPage;