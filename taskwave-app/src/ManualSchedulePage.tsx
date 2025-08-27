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
  const [slots, setSlots] = useState<ScheduleSlot[]>([
    { id: 1, subject_title: '', weekday: '월', start_time: '09:00', end_time: '10:30' },
  ]);
  const [loading, setLoading] = useState(false);

  const handleAddSlot = () => {
    setSlots([...slots, { ...slots[0], id: Date.now() }]);
  };

  const handleSlotChange = (id: number, field: keyof ScheduleSlot, value: string) => {
    setSlots(
      slots.map(slot => (slot.id === id ? { ...slot, [field]: value } : slot))
    );
  };

  const handleRemoveSlot = (id: number) => {
    setSlots(slots.filter(slot => slot.id !== id));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await fetchJSON(EP.SCHEDULES_MANUAL, {
        method: 'POST',
        body: { slots },
      });
      alert('시간표가 성공적으로 저장되었습니다!');
      navigate('/files');
    } catch (err: any) {
      alert(err?.message ?? '저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <Header />
      <main className="manual-schedule-main-content">
        <h1 className="manual-schedule-title">시간표 수동 입력</h1>
        <div className="schedule-form-container">
          {slots.map((slot, index) => (
            <div key={slot.id} className="slot-row">
              <input
                type="text"
                placeholder="과목명"
                value={slot.subject_title}
                onChange={e => handleSlotChange(slot.id, 'subject_title', e.target.value)}
              />
              <select
                value={slot.weekday}
                onChange={e => handleSlotChange(slot.id, 'weekday', e.target.value)}
              >
                {['월', '화', '수', '목', '금', '토', '일'].map(day => (
                  <option key={day} value={day}>{day}</option>
                ))}
              </select>
              <input
                type="time"
                value={slot.start_time}
                onChange={e => handleSlotChange(slot.id, 'start_time', e.target.value)}
              />
              <span>~</span>
              <input
                type="time"
                value={slot.end_time}
                onChange={e => handleSlotChange(slot.id, 'end_time', e.target.value)}
              />
              {slots.length > 1 && (
                <button onClick={() => handleRemoveSlot(slot.id)} className="remove-btn">-</button>
              )}
            </div>
          ))}
          <div className="form-actions">
            <button onClick={handleAddSlot} className="add-btn">+ 강의 추가</button>
            <button onClick={handleSubmit} className="save-btn" disabled={loading}>
              {loading ? '저장 중...' : '시간표 저장'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManualSchedulePage;
