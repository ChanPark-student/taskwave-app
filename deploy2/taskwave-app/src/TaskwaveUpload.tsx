// src/TaskwaveUpload.tsx
import './TaskwaveUpload.css';
import { useState, useEffect, ChangeEvent, DragEvent } from 'react';
import { FiUploadCloud } from 'react-icons/fi';
import Header from './Header';

import { EP } from './lib/endpoints';
import { fetchJSON, authHeaders } from './lib/http';

const TaskwaveUpload = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (selectedFile) {
      const timer = setTimeout(() => {
        // 자동 초기화 로직을 유지하되, 실제 업로드도 수행
        void uploadNow(selectedFile);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [selectedFile]);

  const uploadNow = async (file: File) => {
    try {
      const fd = new FormData();
      fd.append('file', file);
      const data = await fetchJSON<any>(
        EP.TIMETABLE_UPLOAD,
        { method: 'POST', body: fd, headers: { ...authHeaders() } }
      );
      setResult(data);
      console.log('업로드/파싱 결과:', data);
    } catch (err: any) {
      alert(err?.message ?? '업로드 실패');
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type === 'application/pdf' || file.type.startsWith('image/')) {
      setSelectedFile(file);
    } else {
      alert('PDF 또는 이미지 파일만 업로드할 수 있습니다.');
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    if (file.type === 'application/pdf' || file.type.startsWith('image/')) {
      setSelectedFile(file);
    } else {
      alert('PDF 또는 이미지 파일만 업로드할 수 있습니다.');
    }
  };

  return (
    <div className="page">
      <Header />
      <main className="upload-container">
        <h1 className="title">시간표 업로드</h1>
        <div
          className={`drop-zone ${isDragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <FiUploadCloud className="upload-icon" />
          <p>여기에 파일을 드래그하거나, 클릭해서 선택하세요.</p>
          <input type="file" accept=".png,.jpg,.jpeg,.webp,.pdf" onChange={handleFileChange} />
        </div>

        {selectedFile && (
          <div className="file-info">
            <p className="file-name">✅ {selectedFile.name}</p>
            <p className="file-ready-text">파일 업로드 및 분석을 진행합니다…</p>
            <div className="timer-bar-container">
              <div className="timer-bar"></div>
            </div>
          </div>
        )}

        {result && (
          <div className="result-block">
            <h3>분석 결과</h3>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
};

export default TaskwaveUpload;
