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
        void uploadNow(selectedFile);
      }, 3000); // 3초 애니메이션과 시간을 맞춥니다.
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
    } finally {
      // 완료 후 초기화
      setSelectedFile(null);
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

  const handleUploadBoxClick = () => {
    // 파일이 선택된 상태에서는 클릭 이벤트를 무시
    if (selectedFile) return;
    document.getElementById('file-upload')?.click();
  };

  return (
    <div className="page-container">
      <Header />
      <main className="main-content">
        <div
          className={`upload-box ${isDragging ? 'is-dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={handleUploadBoxClick}
          style={{ cursor: selectedFile ? 'default' : 'pointer' }}
        >
          {selectedFile ? (
            <div className="file-info">
              <p className="file-name">✅ {selectedFile.name}</p>
              <p className="file-ready-text">파일 업로드 및 분석을 진행합니다…</p>
              <div className="timer-bar-container">
                <div className="timer-bar"></div>
              </div>
            </div>
          ) : (
            <>
              <h1 className="upload-title">시간표 업로드</h1>
              <FiUploadCloud className="upload-icon" />
              <p className="upload-prompt">여기에 시간표 PDF 또는 이미지 파일을 놓으세요.</p>
              <p className="or-divider">또는</p>
              <div className="upload-button">
                파일 선택
              </div>
              <input
                id="file-upload"
                type="file"
                accept=".png,.jpg,.jpeg,.webp,.pdf"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                onClick={(e) => e.stopPropagation()}
              />
            </>
          )}
        </div>

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