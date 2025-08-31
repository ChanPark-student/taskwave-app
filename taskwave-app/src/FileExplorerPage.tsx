import Header from './Header.tsx';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth, EventInfo, DateInfo } from './context/AuthContext.tsx';
import { FiFolder, FiArrowLeft, FiChevronLeft, FiChevronRight, FiPlusCircle } from 'react-icons/fi';
import './FileExplorerPage.css';
import { useState, useMemo } from 'react';
import AddEventModal from './AddEventModal';

const typeClass = (t: string) => (t || '').toLowerCase();

const CalendarView = ({
  subjectName,
  dates,
  onDayClick,
  onAddEventClick,
}: {
  subjectName: string;
  dates: Record<string, DateInfo>;
  onDayClick: (date: string) => void;
  onAddEventClick: () => void;
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const scheduledDates = useMemo(() => new Set(Object.keys(dates)), [dates]);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  let firstDay = new Date(year, month, 1).getDay();
  firstDay = firstDay === 0 ? 6 : firstDay - 1;

  const calendarDays: JSX.Element[] = [];

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
      <div key={dateStr} className={dayClassName} onClick={() => onDayClick(dateStr)}>
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
        <button onClick={goToPreviousMonth}><FiChevronLeft /></button>
        <h2>{subjectName} - {year}년 {month + 1}월</h2>
        <button onClick={goToNextMonth}><FiChevronRight /></button>
      </div>
      <div className="calendar-actions">
        <button onClick={onAddEventClick} className="add-event-button">
          <FiPlusCircle /> 이벤트 추가
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
  const { subject } = useParams<{ subject: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();

  const [isAddEventModalOpen, setIsAddEventModalOpen] = useState(false);

  const handleDayClick = (dateStr: string) => {
    if (subject) {
      navigate(`/files/${subject}/${dateStr}`);
    }
  };

  const handleAddEventClick = () => {
    setIsAddEventModalOpen(true);
  };

  const handleCloseAddEventModal = () => {
    setIsAddEventModalOpen(false);
  };

  const renderContent = () => {
    if (subject) {
      const subjectData = fileSystem[subject];
      if (!subjectData) return <div className="empty-folder-message">과목 정보를 찾을 수 없습니다.</div>;
      return <CalendarView subjectName={subject} dates={subjectData.dates} onDayClick={handleDayClick} onAddEventClick={handleAddEventClick} />;
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

  const subjectData = subject ? fileSystem[subject] : null;

  return (
    <>
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
        </main>
      </div>
      {isAddEventModalOpen && subjectData && (
        <AddEventModal
          subjectId={subjectData.subject_id}
          onClose={handleCloseAddEventModal}
          refreshMe={refreshMe}
        />
      )}
    </>
  );
};

export default FileExplorerPage;