import { useState, useMemo, useRef, ChangeEvent, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth, AppFileInfo, EventInfo } from './context/AuthContext';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';
import { FiFileText, FiTrash2, FiUploadCloud, FiPlusCircle, FiArrowLeft } from 'react-icons/fi';
import AddEventModal from './AddEventModal';
import Header from './Header';
import './DateDetailPage.css';

const typeKOR = (t: string) => ((t || '').toUpperCase() === 'EXAM' ? '시험' : '과제');

interface EventWithDDay extends EventInfo {
  dDay: number;
}

const DateDetailPage = () => {
  const { subject = '', date = '' } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isAddEventModalOpen, setIsAddEventModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const subjectData = fileSystem[subject];
  const dateInfo = subjectData?.dates[date];

  useEffect(() => {
    if (!subjectData) {
      refreshMe();
    }
  }, [subject, subjectData, refreshMe]);

  const upcomingEvents = useMemo(() => {
    if (!subjectData) return [];
    const allEvents: EventWithDDay[] = [];
    const referenceDate = new Date(date);

    Object.entries(subjectData.dates).forEach(([dateStr, dateInfo]) => {
      dateInfo.events.forEach(event => {
        const eventDate = new Date(dateStr);
        if (eventDate >= referenceDate) {
          const diffTime = eventDate.getTime() - referenceDate.getTime();
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
          allEvents.push({ ...event, dDay: diffDays });
        }
      });
    });
    return allEvents.sort((a, b) => a.dDay - b.dDay);
  }, [subjectData, date]);

  const handleDeleteFile = async (fileId: string) => {
    if (window.confirm('정말로 이 파일을 삭제하시겠습니까?')) {
      try {
        await fetchJSON(EP.MATERIAL_DELETE(fileId), { method: 'DELETE' });
        refreshMe();
      } catch (error) {
        alert('파일 삭제에 실패했습니다.');
      }
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !subjectData) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject_id', subjectData.subject_id);
    formData.append('date', date);
    try {
      await fetchJSON(EP.MATERIALS_UPLOAD, { method: 'POST', body: formData });
      refreshMe();
    } catch (error) {
      alert('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (window.confirm('정말로 이 이벤트를 삭제하시겠습니까?')) {
      try {
        await fetchJSON(EP.EVENT_DELETE(eventId), { method: 'DELETE' });
        refreshMe();
      } catch (error) {
        alert('이벤트 삭제에 실패했습니다.');
      }
    }
  };

  if (!subjectData) {
    return (
        <div className="page-container">
            <Header />
            <main className="main-content"><p>로딩 중...</p></main>
        </div>
    )
  }

  return (
    <div className="page-container date-detail-page">
      <Header />
      <main className="main-content">
        <div className="explorer-box" style={{maxWidth: '1000px'}}>
            <div className="explorer-header">
                <button onClick={() => navigate(`/files/${subject}`)} className="back-button" title="달력으로 돌아가기">
                    <FiArrowLeft />
                </button>
                <h3>{date} ({subject})</h3>
            </div>
            <div className="modal-body-grid">
                {/* Left Panel: File Management */}
                <div className="panel file-panel">
                <div className="panel-header">
                    <h4>파일 현황</h4>
                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} style={{ display: 'none' }} disabled={isUploading} />
                    <button onClick={() => fileInputRef.current?.click()} className="panel-button" disabled={isUploading}>
                    <FiUploadCloud /> {isUploading ? '업로드 중...' : '업로드'}
                    </button>
                </div>
                <div className="item-list">
                    {dateInfo?.files && dateInfo.files.length > 0 ? (
                    dateInfo.files.map((file: AppFileInfo) => (
                        <div key={file.id} className="list-item">
                        <a href={file.file_url} target="_blank" rel="noopener noreferrer" className="item-link">
                            <FiFileText />
                            <span>{file.name}</span>
                        </a>
                        <button onClick={() => handleDeleteFile(file.id.toString())} className="delete-item-button"><FiTrash2 /></button>
                        </div>
                    ))
                    ) : (
                    <div className="empty-message-box">파일이 없습니다.</div>
                    )}
                </div>
                </div>

                {/* Right Panel: Upcoming Events */}
                <div className="panel event-panel">
                <div className="panel-header">
                    <h4>이벤트 목록 (D-Day)</h4>
                    <button onClick={() => setIsAddEventModalOpen(true)} className="panel-button">
                    <FiPlusCircle /> 이벤트 추가
                    </button>
                </div>
                <div className="item-list">
                    {upcomingEvents.length > 0 ? (
                    upcomingEvents.map(event => (
                        <div key={event.id} className="list-item event-list-item">
                        <div className="event-d-day">D-{event.dDay}</div>
                        <div className="event-details">
                            <span className="event-title">{event.title}</span>
                            <span className="event-type">({typeKOR(event.event_type as string)})</span>
                        </div>
                        {/* Add delete button here */}
                        <button onClick={() => handleDeleteEvent(event.id)} className="delete-item-button"><FiTrash2 /></button>
                        </div>
                    ))
                    ) : (
                    <div className="empty-message-box">예정된 이벤트가 없습니다.</div>
                    )}
                </div>
                </div>
            </div>
        </div>
      </main>

      {isAddEventModalOpen && (
        <AddEventModal
          subjectId={subjectData.subject_id}
          date={date} // Add event for the selected date
          onClose={() => setIsAddEventModalOpen(false)}
          refreshMe={() => {
            setIsAddEventModalOpen(false);
            refreshMe();
          }}
        />
      )}
    </div>
  );
};

export default DateDetailPage;