import { useState, useEffect, ChangeEvent, DragEvent } from 'react'; // ChangeEvent, DragEvent 타입 임포트
import { FiUploadCloud } from 'react-icons/fi';
import Header from './Header.tsx';
import { useAuth } from './context/AuthContext.tsx';
import './TaskwaveUpload.css';

const TaskwaveUpload = () => {
  const { user } = useAuth(); 
  
  // selectedFile의 타입을 File 또는 null로 지정
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (selectedFile) {
      const timer = setTimeout(() => {
        setSelectedFile(null);
      }, 3000); 
      return () => clearTimeout(timer);
    }
  }, [selectedFile]);

  // file 매개변수의 타입을 File로 지정
  const processFile = (file: File) => {
    if (!user) {
      alert('로그인 후 이용해주세요.');
      return;
    }

    if (file && (file.type === 'application/pdf' || file.type.startsWith('image/'))) {
      setSelectedFile(file);
      console.log('선택된 파일:', file.name);
    } else {
      alert('PDF 또는 이미지 파일만 업로드할 수 있습니다.');
    }
  };

  // e 매개변수의 타입을 ChangeEvent로 지정
  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  // 드래그 이벤트들의 e 매개변수 타입을 DragEvent로 지정
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => { 
    e.preventDefault(); 
    e.stopPropagation(); 
    setIsDragging(true); 
  };
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => { 
    e.preventDefault(); 
    e.stopPropagation(); 
    setIsDragging(false); 
  };
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  };

  return (
    <div className="page-container">
      <Header />
      <main className="main-content">
        <div
          className={`upload-box ${isDragging ? 'is-dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {!selectedFile ? (
            <>
              <h1 className="upload-title">파일 업로드</h1>
              <FiUploadCloud className="upload-icon" />
              <p className="upload-prompt">여기에 PDF 또는 이미지 파일 놓기</p>
              <span className="or-divider">또는</span>
              <label htmlFor="file-upload" className="upload-button">
                업로드하여 편집
              </label>
              <input
                id="file-upload"
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </>
          ) : (
            <div className="file-info">
              <p className="file-name">✅ {selectedFile.name}</p>
              <p className="file-ready-text">파일이 업로드되었습니다.</p>
              <div className="timer-bar-container">
                <div className="timer-bar"></div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default TaskwaveUpload;