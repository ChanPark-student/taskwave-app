import { useState, FormEvent } from 'react';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';
import { FiX } from 'react-icons/fi';
import './AddEventModal.css';

interface AddEventModalProps {
  subjectId: string;
  date: string;
  onClose: () => void;
  refreshMe: () => void;
}

const AddEventModal = ({ subjectId, date, onClose, refreshMe }: AddEventModalProps) => {
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventWarningDays, setNewEventWarningDays] = useState<number>(0);
  const [newEventEventType, setNewEventEventType] = useState<'exam' | 'assignment'>('exam');

  const handleAddEvent = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await fetchJSON(EP.EVENTS, {
        method: 'POST',
        body: JSON.stringify({
          subject_id: subjectId,
          title: newEventTitle,
          event_type: newEventEventType,
          date,
          warning_days: Number.isFinite(newEventWarningDays) ? newEventWarningDays : 0,
        }),
      });
      onClose();
      refreshMe();
    } catch (error) {
      console.error('Failed to add event:', error);
      alert('이벤트 추가에 실패했습니다.');
    }
  };

  return (
    <div className="add-event-modal-component">
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>새 이벤트 추가</h3>
            <button onClick={onClose} className="close-button">
              <FiX />
            </button>
          </div>
          <div className="modal-body">
              <div className="add-event-buttons" style={{ marginBottom: '20px' }}>
                  <button 
                      className={newEventEventType === 'exam' ? 'active' : ''}
                      onClick={() => setNewEventEventType('exam')}
                  >시험</button>
                  <button 
                      className={newEventEventType === 'assignment' ? 'active' : ''}
                      onClick={() => setNewEventEventType('assignment')}
                  >과제</button>
              </div>
              <form onSubmit={handleAddEvent} className="add-event-form">
              <h4>새 {newEventEventType === 'exam' ? '시험' : '과제'} 정보</h4>
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
                  <button type="button" onClick={onClose}>취소</button>
              </div>
              </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddEventModal;