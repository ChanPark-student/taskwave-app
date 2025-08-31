import { useState, FormEvent, useEffect, useRef, ChangeEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from './Header';
import { useAuth, FileInfo, EventInfo } from './context/AuthContext';
import { EP } from './lib/endpoints';
import { fetchJSON, postWithBody } from './lib/http';
import { FiFileText, FiTrash2, FiArrowLeft, FiUploadCloud, FiPlusCircle, FiCalendar, FiFile } from 'react-icons/fi';
import AddEventModal from './AddEventModal';
import './DateDetailPage.css'; // Import new CSS

const typeKOR = (t: string) => ((t || '').toUpperCase() === 'EXAM' ? '시험' : '과제');
const typeClass = (t: string) => (t || '').toLowerCase();

const DateDetailPage = () => {
  const { subject = '', date = '' } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const subjectData = fileSystem[subject];
  const dateInfo = subjectData?.dates[date];

  useEffect(() => {
    if (!subjectData || !dateInfo) {
      refreshMe();
    }
  }, [subject, date, subjectData, dateInfo, refreshMe]);

  const handleDeleteFile = async (fileId: string) => {
    if (window.confirm('정말로 이 파일을 삭제하시겠습니까?')) {
      try {
        await fetchJSON(EP.MATERIAL_DELETE(fileId), { method: 'DELETE' });
        refreshMe();
      } catch (error) {
        console.error('Failed to delete file:', error);
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
      // fetchJSON handles FormData correctly, so we can use it directly
      await fetchJSON(EP.MATERIALS_UPLOAD, {
        method: 'POST',
        body: formData,
      });
      refreshMe();
    } catch (error) {
      console.error('Failed to upload file:', error);
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
    <>
      <div className="page-container">
        <Header />
        <main className="main-content">
          <div className="explorer-box" style={{ maxWidth: '1000px', margin: 'auto' }}>
            <div className="explorer-header">
              <button onClick={() => navigate(`/files/${subject}`)} className="back-button" title="달력으로 돌아가기">
                <FiArrowLeft />
              </button>
              <h3>{date} ({subject})</h3>
            </div>

            <div className="date-detail-grid">
              {/* File Management Panel */}
              <div className="management-panel">
                <div className="panel-header">
                  <h4><FiFile /> 파일 관리</h4>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    disabled={isUploading}
                  />
                  <button onClick={() => fileInputRef.current?.click()} className="panel-button" disabled={isUploading}>
                    <FiUploadCloud /> {isUploading ? '업로드 중...' : '업로드'}
                  </button>
                </div>
                <div className="item-list">
                  {dateInfo.files.length > 0 ? (
                    dateInfo.files.map((file: FileInfo) => (
                      <div key={file.id} className="list-item">
                        <a href={file.file_url} target="_blank" rel="noopener noreferrer" className="item-link">
                          <FiFileText />
                          <span>{file.name}</span>
                        </a>
                        <button onClick={() => handleDeleteFile(file.id)} className="delete-item-button">
                          <FiTrash2 />
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className="empty-message-box">파일이 없습니다.</div>
                  )}
                </div>
              </div>

              {/* Event Management Panel */}
              <div className="management-panel">
                <div className="panel-header">
                  <h4><FiCalendar /> 이벤트 관리</h4>
                  <button onClick={() => setIsEventModalOpen(true)} className="panel-button">
                    <FiPlusCircle /> 이벤트 추가
                  </button>
                </div>
                <div className="item-list">
                  {dateInfo.events.length > 0 ? (
                    dateInfo.events.map((event: EventInfo) => (
                      <div key={event.id} className={`list-item ${typeClass(event.event_type as unknown as string)}`}>
                        <span className="item-link">
                          {event.title} ({typeKOR(event.event_type as unknown as string)})
                        </span>
                        <button onClick={() => handleDeleteEvent(event.id)} className="delete-item-button">
                          <FiTrash2 />
                        </button>
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
      </div>

      {isEventModalOpen && (
        <AddEventModal
          subjectId={subjectData.subject_id}
          date={date}
          onClose={() => setIsEventModalOpen(false)}
          refreshMe={refreshMe}
        />
      )}
    </>
  );
};

export default DateDetailPage;