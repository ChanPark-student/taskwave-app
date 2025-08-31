import { useState, useMemo, useRef, ChangeEvent } from 'react';
import { useAuth, FileInfo, EventInfo } from './context/AuthContext';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';
import { FiX, FiFileText, FiTrash2, FiUploadCloud, FiPlusCircle } from 'react-icons/fi';
import AddEventModal from './AddEventModal'; // The smaller modal for adding events
import './DateDetailModal.css';

const typeKOR = (t: string) => ((t || '').toUpperCase() === 'EXAM' ? '시험' : '과제');

interface EventWithDDay extends EventInfo {
  dDay: number;
}

interface DateDetailModalProps {
  subjectName: string;
  subjectId: string;
  selectedDate: string; // The date clicked on the calendar
  onClose: () => void;
  refreshMe: () => void;
}

const DateDetailModal = ({ subjectName, subjectId, selectedDate, onClose, refreshMe }: DateDetailModalProps) => {
  const { fileSystem } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isAddEventModalOpen, setIsAddEventModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // --- Data for the selected date ---
  const subjectData = fileSystem[subjectName];
  const dateInfo = subjectData?.dates[selectedDate];

  // --- Upcoming events calculation ---
  const upcomingEvents = useMemo(() => {
    if (!subjectData) return [];
    const allEvents: EventWithDDay[] = [];
    const referenceDate = new Date(selectedDate);

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
  }, [subjectData, selectedDate]);

  // --- Handlers ---
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
    if (!file) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject_id', subjectId);
    formData.append('date', selectedDate);
    try {
      await fetchJSON(EP.MATERIALS_UPLOAD, { method: 'POST', body: formData });
      refreshMe();
    } catch (error) {
      alert('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="date-detail-modal">
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>{selectedDate} ({subjectName})</h3>
            <button onClick={onClose} className="close-button"><FiX /></button>
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
                  dateInfo.files.map((file: FileInfo) => (
                    <div key={file.id} className="list-item">
                      <a href={file.file_url} target="_blank" rel="noopener noreferrer" className="item-link">
                        <FiFileText />
                        <span>{file.name}</span>
                      </a>
                      <button onClick={() => handleDeleteFile(file.id)} className="delete-item-button"><FiTrash2 /></button>
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
                    </div>
                  ))
                ) : (
                  <div className="empty-message-box">예정된 이벤트가 없습니다.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {isAddEventModalOpen && (
        <AddEventModal
          subjectId={subjectId}
          date={selectedDate} // Add event for the selected date
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

export default DateDetailModal;
