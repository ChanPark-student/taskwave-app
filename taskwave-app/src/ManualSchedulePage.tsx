// src/ManualSchedulePage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';
import './ManualSchedulePage.css';

interface ScheduleSlot {
  id: number;
  subject_title: string;
  weekday: string;
  start_time: string;
  end_time: string;
}

const ManualSchedulePage = () => {
  const navigate = useNavigate();
  
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
      const response = await fetchJSON<{ status: string; message: string }>(
        EP.SCHEDULES_SCRAPE_AND_GENERATE, 
        { method: 'POST', body: { url, start_date: startDate, end_date: endDate } }
      );
      setSuccessMessage(response.message || 'URL에서 시간표를 성공적으로 가져왔습니다!');
      setTimeout(() => navigate('/files'), 2000);
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
      await fetchJSON(EP.SCHEDULES_MANUAL, { method: 'POST', body: { slots } });
      setSuccessMessage('시간표가 성공적으로 저장되었습니다!');
      setTimeout(() => navigate('/files'), 2000);
    } catch (err: any) {
      setError(err?.message ?? '저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <Header />
      <main className="manual-schedule-main-content">
        <h1 className="manual-schedule-title">시간표 추가하기</h1>

        <div className="import-section url-import-section">
          <h2>URL에서 가져오기</h2>
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
          <h2>수동으로 입력하기</h2>
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

      </main>
    </div>
  );
};

export default ManualSchedulePage;
