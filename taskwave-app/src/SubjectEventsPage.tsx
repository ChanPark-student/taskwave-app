import { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from './Header';
import { useAuth, EventInfo } from './context/AuthContext';
import { FiArrowLeft, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';
import './SubjectEventsPage.css';
//11
const typeKOR = (t: string) => ((t || '').toUpperCase() === 'EXAM' ? '시험' : '과제');

interface EventWithDDay extends EventInfo {
  dDay: number;
  date: string;
}

const SubjectEventsPage = () => {
  const { subject = '' } = useParams<{ subject: string }>();
  const navigate = useNavigate();
  const { fileSystem } = useAuth();

  const subjectData = fileSystem[subject];

  const upcomingEvents = useMemo(() => {
    if (!subjectData) return [];

    const allEvents: EventWithDDay[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    Object.entries(subjectData.dates).forEach(([date, dateInfo]) => {
      dateInfo.events.forEach(event => {
        const eventDate = new Date(date);
        const diffTime = eventDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays >= 0) {
          allEvents.push({ ...event, date, dDay: diffDays });
        }
      });
    });

    return allEvents.sort((a, b) => a.dDay - b.dDay);
  }, [subjectData]);

  if (!subjectData) {
    return (
      <div className="page-container">
        <Header />
        <main className="main-content">
          <p>과목 정보를 찾을 수 없습니다.</p>
          <button onClick={() => navigate(-1)}>뒤로 가기</button>
        </main>
      </div>
    );
  }

  return (
    <div className="page-container subject-events-page">
      <Header />
      <main className="main-content">
        <div className="explorer-box" style={{ maxWidth: '800px', margin: 'auto' }}>
          <div className="explorer-header">
            <button onClick={() => navigate(`/files/${subject}`)} className="back-button" title="달력으로 돌아가기">
              <FiArrowLeft />
            </button>
            <h3>{subject} - 전체 이벤트 목록</h3>
          </div>

          <div className="event-list-container">
            {upcomingEvents.length > 0 ? (
              upcomingEvents.map(event => (
                <div key={event.id} className="event-list-item">
                  <div className="event-d-day">
                    {event.dDay === 0 ? (
                        <><FiAlertTriangle color="red"/> D-Day</>
                    ) : (
                        <><FiCheckCircle color="green"/> D-{event.dDay}</>
                    )}
                  </div>
                  <div className="event-details">
                    <span className="event-title">{event.title}</span>
                    <span className="event-type">({typeKOR(event.event_type as string)})</span>
                  </div>
                  <div className="event-date">{event.date}</div>
                </div>
              ))
            ) : (
              <p className="empty-message-box">예정된 이벤트가 없습니다.</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default SubjectEventsPage;
