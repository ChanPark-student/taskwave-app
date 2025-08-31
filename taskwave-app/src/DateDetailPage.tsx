// src/DateDetailPage.tsx
import { useState, FormEvent, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from './Header';
import { useAuth, FileInfo, EventInfo } from './context/AuthContext';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';
import { FiFileText, FiTrash2, FiArrowLeft } from 'react-icons/fi';
import './FileExplorerPage.css'; // Reuse styles for now

const typeKOR = (t: string) => ((t || '').toUpperCase() === 'EXAM' ? '시험' : '과제');
const typeClass = (t: string) => (t || '').toLowerCase();

const DateDetailPage = () => {
  const { subject = '', date = '' } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();

  const [showAddEventForm, setShowAddEventForm] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventWarningDays, setNewEventWarningDays] = useState<number>(0);
  const [newEventEventType, setNewEventEventType] = useState<'exam' | 'assignment'>('exam');

  const subjectData = fileSystem[subject];
  const dateInfo = subjectData?.dates[date];

  useEffect(() => {
    if (!subjectData || !dateInfo) {
      // Initial load might not have the data, refresh might be needed
      refreshMe();
    }
  }, [subject, date, subjectData, dateInfo, refreshMe]);


  const handleAddEvent = async (e: FormEvent) => {
    e.preventDefault();
    if (!subjectData) return;

    try {
      await fetchJSON(EP.EVENTS, {
        method: 'POST',
        body: JSON.stringify({
          subject_id: subjectData.subject_id,
          title: newEventTitle,
          event_type: newEventEventType,
          date,
          warning_days: Number.isFinite(newEventWarningDays) ? newEventWarningDays : 0,
        }),
      });
      setShowAddEventForm(false);
      setNewEventTitle('');
      setNewEventWarningDays(0);
      refreshMe(); // Refresh data
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
        refreshMe();
      } catch (error) {
        console.error('Failed to delete event:', error);
        alert('이벤트 삭제에 실패했습니다.');
      }
    }
  };

  if (!subjectData || !dateInfo) {
    return (
      <div className="page-container">
        <Header />
        <main className="main-content">
          <p>데이터를 불러오는 중... 또는 잘못된 접근입니다.</p>
          <button onClick={() => navigate(-1)}>뒤로 가기</button>
        </main>
      </div>
    );
  }

  return (
    <div className="page-container">
      <Header />
      <main className="main-content">
        <div className="explorer-box" style={{ maxWidth: '800px', margin: 'auto' }}>
           <div className="explorer-header">
            <button onClick={() => navigate(`/files/${subject}`)} className="back-button" title="달력으로 돌아가기">
              <FiArrowLeft />
            </button>
            <h3>{date} ({subject})</h3>
          </div>
          <div className="modal-body" style={{ padding: '20px' }}>
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
                    setNewEventEventType('exam');
                    setShowAddEventForm(true);
                  }}
                >
                  시험 추가
                </button>
                <button
                  onClick={() => {
                    setNewEventEventType('assignment');
                    setShowAddEventForm(true);
                  }}
                >
                  과제 추가
                </button>
              </div>
              {showAddEventForm && (
                <form onSubmit={handleAddEvent} className="add-event-form">
                  <h4>새 {newEventEventType === 'exam' ? '시험' : '과제'} 추가</h4>
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
      </main>
    </div>
  );
};

export default DateDetailPage;
