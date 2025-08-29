import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext.tsx';
import Header from './Header.tsx';
import { FiFolder, FiFileText, FiArrowLeft, FiUpload } from 'react-icons/fi';
import './FileExplorerPage.css';
import { useRef, useState, ChangeEvent } from 'react';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';

const FileExplorerPage = () => {
  const { subject, date } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleGoBack = () => navigate(-1);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !subject || !date) return;

    const subjectData = fileSystem[subject];
    const dateData = subjectData?.dates?.[date];
    if (!subjectData || !dateData) {
      setUploadError('업로드에 필요한 ID 정보를 찾을 수 없습니다.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject_id', subjectData.subject_id);
    formData.append('session_id', dateData.session_id);
    formData.append('name', file.name);

    try {
      await fetchJSON(EP.MATERIALS_UPLOAD, {
        method: 'POST',
        body: formData,
        // fetchJSON은 자동으로 토큰을 추가하지만, FormData는 Content-Type을 설정하지 않아야 브라우저가 올바르게 처리합니다.
      });
      await refreshMe(); // 파일 목록을 다시 불러오기 위해 전체 데이터 새로고침
    } catch (err) {
      console.error("File upload failed:", err);
      setUploadError('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  const renderContent = () => {
    // 2단계: 날짜 폴더 내부 (파일 목록)
    if (subject && date) {
      const dateInfo = fileSystem[subject]?.dates?.[date];
      const files = dateInfo?.files || [];

      return (
        <>
          <div className="upload-button-container">
            <button onClick={handleUploadClick} disabled={isUploading} className="upload-button-in-view">
              <FiUpload />
              {isUploading ? '업로드 중...' : '파일 업로드'}
            </button>
            <input type="file" ref={fileInputRef} onChange={handleFileSelected} style={{ display: 'none' }} />
          </div>
          {uploadError && <div className="upload-error">{uploadError}</div>}
          {files.length === 0 ? (
            <div className="empty-folder-message">업로드된 파일이 없습니다.</div>
          ) : (
            files.map(file => (
              <a href={file.file_url} target="_blank" rel="noopener noreferrer" key={file.id} className="folder-item file-item">
                <FiFileText />
                <span>{file.name}</span>
              </a>
            ))
          )}
        </>
      );
    }
    
    // 1단계: 과목 폴더 내부 (날짜 폴더 목록)
    if (subject) {
      const dates = fileSystem[subject]?.dates || {};
      const dateKeys = Object.keys(dates);
      if (dateKeys.length === 0) return <div className="empty-folder-message">생성된 날짜 폴더가 없습니다.</div>;

      return dateKeys.map(dateKey => (
        <Link to={`/files/${subject}/${dateKey}`} key={dateKey} className="folder-item">
          <FiFolder />
          <span>{dateKey}</span>
        </Link>
      ));
    }

    // 최상위: 모든 과목 폴더
    return Object.keys(fileSystem).map(subjectName => (
      <Link to={`/files/${subjectName}`} key={subjectName} className="folder-item">
        <FiFolder />
        <span>{subjectName}</span>
      </Link>
    ));
  };

  const Breadcrumbs = () => (
    <div className="breadcrumbs">
      <Link to="/files">내 파일</Link>
      {subject && <><span>&gt;</span><Link to={`/files/${subject}`}>{subject}</Link></>}
      {date && <><span>&gt;</span><span>{date}</span></>}
    </div>
  );

  return (
    <div className="page-container">
      <Header />
      <main className="main-content">
        <div className="explorer-box">
          <div className="explorer-header">
            <button onClick={handleGoBack} className="back-button" title="뒤로가기">
              <FiArrowLeft />
            </button>
            <Breadcrumbs />
          </div>
          <div className="grid-container">
            {renderContent()}
          </div>
        </div>
      </main>
    </div>
  );
};

export default FileExplorerPage;
