import Header from './Header.tsx';

import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth, FileInfo, EventInfo, DateInfo, SubjectInfo } from './context/AuthContext.tsx';
import { FiFolder, FiFileText, FiArrowLeft, FiUpload, FiChevronLeft, FiChevronRight, FiTrash2, FiX, FiPlus } from 'react-icons/fi';
import './FileExplorerPage.css';
import { useRef, useState, ChangeEvent, useMemo, FormEvent } from 'react';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';

// --- Small helpers ---
const normType = (t: string) => (t || '').toUpperCase() as 'EXAM' | 'ASSIGNMENT';
const typeKOR = (t: string) => (normType(t) === 'EXAM' ? '시험' : '과제');
const typeClass = (t: string) => normType(t).toLowerCase(); // "exam" | "assignment"

// --- Helper Components ---

const DayDetailModal = ({
  subjectName,
  subjectId,
  date,
  dateInfo,
  onClose,
  refreshMe,
}: {
  subjectName: string;
  subjectId: string;
  date: string;
  dateInfo: DateInfo;
  onClose: () => void;
  refreshMe: () => void;
}) => {
  const [showAddEventForm, setShowAddEventForm] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventWarningDays, setNewEventWarningDays] = useState<number>(0);
  const [newEventEventType, setNewEventEventType] = useState<'EXAM' | 'ASSIGNMENT'>('EXAM');

  const handleAddEvent = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await fetchJSON(EP.EVENTS, {
        method: 'POST',
        body: JSON.stringify({
          subject_id: subjectId,
          title: newEventTitle,
          event_type: newEventEventType, // send as 'EXAM' | 'ASSIGNMENT'
          date,
          warning_days: Number.isFinite(newEventWarningDays) ? newEventWarningDays : 0,
        }),
      });
      onClose(); // Close modal after adding
      refreshMe(); // Refresh data after adding event
    } catch (error) {
      console.error('Failed to add event:', error);
      alert('이벤트 추가에 실패했습니다.');
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (window.confirm('정말로 이 이벤트를 삭제하시겠습니까?')) {
      try {
        await fetchJSON(EP.EVENT_DELETE(eventId), {
          method: 'DELETE',
        });
        onClose();
        refreshMe();
      } catch (error) {
        console.error('Failed to delete event:', error);
        alert('이벤트 삭제에 실패했습니다.');
      }
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            {date} ({subjectName})
          </h3>
          <button onClick={onClose} className="close-button">
            <FiX />
          </button>
        </div>
        <div className="modal-body">
          <div className="modal-section">
            <h4>파일 목록</h4>
            <div className="file-list-in-modal">
              {dateInfo.files.length > 0 ? (
                dateInfo.files.map((file: FileInfo) => (
                  <div key={file.id} className="file-item-container">
                    <a href={file.file_url} target="_blank" rel="noopener noreferrer" className="file-link">
                      <FiFileText />
                      <span>{file.name}</span>
                    </a>
                  </div>
                ))
              ) : (
                <p className="empty-message">파일이 없습니다.</p>
              )}
            </div>
          </div>
          <div className="modal-section">
            <h4>이벤트 (시험/과제)</h4>
            <div className="event-list-in-modal">
              {dateInfo.events.length > 0 ? (
                dateInfo.events.map((event: EventInfo) => (
                  <div key={event.id} className={`event-item ${typeClass(event.event_type as unknown as string)}`}>
                    <span>
                      {event.title} ({typeKOR(event.event_type as unknown as string)})
                    </span>
                    <button className="delete-event-button" onClick={() => handleDeleteEvent(event.id)}>
                      <FiTrash2 />
                    </button>
                  </div>
                ))
              ) : (
                <p className="empty-message">예정된 이벤트가 없습니다.</p>
              )}
            </div>
            <div className="add-event-buttons">
              <button
                onClick={() => {
                  setNewEventEventType('EXAM');
                  setShowAddEventForm(true);
                }}
              >
                시험 추가
              </button>
              <button
                onClick={() => {
                  setNewEventEventType('ASSIGNMENT');
                  setShowAddEventForm(true);
                }}
              >
                과제 추가
              </button>
            </div>
            {showAddEventForm && (
              <form onSubmit={handleAddEvent} className="add-event-form">
                <h4>새 {newEventEventType === 'EXAM' ? '시험' : '과제'} 추가</h4>
                <div className="form-group">
                  <label htmlFor="eventTitle">제목:</label>
                  <input
                    id="eventTitle"
                    type="text"
                    value={newEventTitle}
                    onChange={e => setNewEventTitle(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="warningDays">경고일 (D-day):</label>
                  <input
                    id="warningDays"
                    type="number"
                    value={newEventWarningDays}
                    onChange={e => {
                      const v = parseInt(e.target.value, 10);
                      setNewEventWarningDays(Number.isNaN(v) ? 0 : v);
                    }}
                    min={0}
                  />
                </div>
                <div className="form-actions">
                  <button type="submit">추가</button>
                  <button type="button" onClick={() => setShowAddEventForm(false)}>
                    취소
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const CalendarView = ({
  subjectName,
  dates,
  onDayClick,
}: {
  subjectName: string;
  dates: Record<string, DateInfo>;
  onDayClick: (date: string) => void;
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const scheduledDates = useMemo(() => new Set(Object.keys(dates)), [dates]);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  let firstDay = new Date(year, month, 1).getDay();
  // convert Sunday=0 to 6, Mon=1→0, ... (Mon-start calendar)
  firstDay = firstDay === 0 ? 6 : firstDay - 1;

  const calendarDays: JSX.Element[] = [];

  // leading empty cells
  for (let i = 0; i < firstDay; i++) {
    calendarDays.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const dateInfo = dates[dateStr];
    const hasSchedule = scheduledDates.has(dateStr);
    const hasFiles = hasSchedule && (dateInfo?.files?.length ?? 0) > 0;
    const events: EventInfo[] = hasSchedule ? dateInfo?.events || [] : [];

    let dayClassName = 'calendar-day';
    if (hasSchedule) {
      dayClassName += ' has-schedule';
      dayClassName += hasFiles ? ' has-files' : ' no-files';
    }

    calendarDays.push(
      <div key={dateStr} className={dayClassName} onClick={() => hasSchedule && onDayClick(dateStr)}>
        <div className="day-link">
          <span className="day-number">{day}</span>
          <div className="event-markers">
            {events.map((event: EventInfo) => (
              <div
                key={event.id}
                className={`event-dot ${typeClass(event.event_type as unknown as string)}`}
                title={event.title}
              ></div>
            ))}
          </div>
        </div>
      </div>,
    );
  }

  const goToPreviousMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const goToNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <button onClick={goToPreviousMonth}>
          <FiChevronLeft />
        </button>
        <h2>
          {year}년 {month + 1}월
        </h2>
        <button onClick={goToNextMonth}>
          <FiChevronRight />
        </button>
      </div>
      <div className="calendar-grid">
        <div className="day-name">월</div>
        <div className="day-name">화</div>
        <div className="day-name">수</div>
        <div className="day-name">목</div>
        <div className="day-name">금</div>
        <div className="day-name">토</div>
        <div className="day-name">일</div>
        {calendarDays}
      </div>
    </div>
  );
};

const FileExplorerPage = () => {
  const { subject, date } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const handleDayClick = (dateStr: string) => {
    setSelectedDate(dateStr);
  };

  const handleCloseModal = () => {
    setSelectedDate(null);
  };

  const renderContent = () => {
    if (subject) {
      const subjectData = fileSystem[subject];
      if (!subjectData) return <div className="empty-folder-message">과목 정보를 찾을 수 없습니다.</div>;
      return <CalendarView subjectName={subject} dates={subjectData.dates} onDayClick={handleDayClick} />;
    } else {
      const subjectFolders: JSX.Element[] = Object.keys(fileSystem)
        .filter(name => name.toLowerCase() !== 'etc')
        .map(subjectName => (
          <Link to={`/files/${subjectName}`} key={subjectName} className="folder-item">
            <FiFolder />
            <span>{subjectName}</span>
          </Link>
        ));

      if (fileSystem['etc']) {
        subjectFolders.push(
          <Link to="/files/etc" key="etc" className="folder-item">
            <FiFolder />
            <span>etc</span>
          </Link>,
        );
      }
      return subjectFolders;
    }
  };

  const selectedSubjectData = subject ? fileSystem[subject] : null;
  const selectedDateInfo =
    selectedDate && selectedSubjectData ? selectedSubjectData.dates[selectedDate] : (null as DateInfo | null);

  return (
    <div className="page-container">
      <Header />
      <main className="main-content">
        <div className="explorer-box">
          <div className="explorer-header">
            <button onClick={() => navigate(-1)} className="back-button" title="뒤로가기">
              <FiArrowLeft />
            </button>
            <div className="breadcrumbs">
              <Link to="/files">내 파일</Link>
              {subject && (
                <>
                  <span>&gt;</span>
                  <Link to={`/files/${subject}`}>{subject}</Link>
                </>
              )}
            </div>
          </div>
          <div className={subject ? 'grid-container-calendar' : 'grid-container-subjects'}>{renderContent()}</div>
        </div>
        {subject && selectedDate && selectedDateInfo && selectedSubjectData && (
          <DayDetailModal
            subjectName={subject}
            subjectId={selectedSubjectData.subject_id}
            date={selectedDate}
            dateInfo={selectedDateInfo}
            onClose={() => {
              handleCloseModal();
              refreshMe(); // after closing modal
            }}
            refreshMe={refreshMe}
          />
        )}
      </main>
    </div>
  );
};

export default FileExplorerPage;
