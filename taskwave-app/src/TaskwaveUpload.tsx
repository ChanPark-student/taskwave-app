// src/TaskwaveUpload.tsx
import './TaskwaveUpload.css';
import { useState, ChangeEvent, DragEvent } from 'react';
import { FiUploadCloud, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';
import Header from './Header';
import { useAuth } from './context/AuthContext';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';

const TaskwaveUpload = () => {
  const { refreshMe } = useAuth(); // 파일 목록 새로고침을 위해 AuthContext 사용
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [fileName, setFileName] = useState('');

  const handleAutoSortUpload = async (file: File) => {
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('idle');
    setFileName(file.name);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('last_modified', String(file.lastModified));

    try {
      await fetchJSON(EP.UPLOADS_AUTO_SORT, {
        method: 'POST',
        body: formData,
      });
      setUploadStatus('success');
      await refreshMe(); // 성공 시 파일 탐색기 데이터 새로고침
    } catch (err: any) {
      console.error('Auto-sort upload failed:', err);
      setUploadStatus('error');
    } finally {
      setIsUploading(false);
      // 3초 후 상태 초기화
      setTimeout(() => {
        setUploadStatus('idle');
        setFileName('');
      }, 3000);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      void handleAutoSortUpload(file);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      void handleAutoSortUpload(file);
    }
  };

  const renderUploadState = () => {
    if (isUploading) {
      return (
        <div className="file-info">
          <p className="file-name">{fileName}</p>
          <p className="file-ready-text">파일 업로드 및 자동 분류 중...</p>
          <div className="timer-bar-container">
            <div className="timer-bar"></div>
          </div>
        </div>
      );
    }

    if (uploadStatus === 'success') {
      return (
        <div className="file-info success">
          <FiCheckCircle />
          <p>성공적으로 업로드 및 분류되었습니다!</p>
        </div>
      );
    }

    if (uploadStatus === 'error') {
      return (
        <div className="file-info error">
          <FiAlertCircle />
          <p>업로드에 실패했습니다. 다시 시도해주세요.</p>
        </div>
      );
    }

    return (
      <>
        <h1 className="upload-title">파일 자동 분류</h1>
        <FiUploadCloud className="upload-icon" />
        <p className="upload-prompt">여기에 파일을 놓으면 수정 시간을 기준으로 자동 분류됩니다.</p>
        <p className="or-divider">또는</p>
        <label htmlFor="file-upload" className="upload-button">
          파일 선택
        </label>
        <input
          id="file-upload"
          type="file"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          onClick={(e) => e.stopPropagation()}
        />
      </>
    );
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
          onClick={() => document.getElementById('file-upload')?.click()}
          style={{ cursor: isUploading ? 'default' : 'pointer' }}
        >
          {renderUploadState()}
        </div>
      </main>
    </div>
  );
};

export default TaskwaveUpload;
