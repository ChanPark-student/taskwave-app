import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext.tsx';
import Header from './Header.tsx';
import { FiFolder, FiFileText, FiArrowLeft } from 'react-icons/fi';
import './FileExplorerPage.css';

const FileExplorerPage = () => {
  // 라우트 파라미터를 새로운 구조에 맞게 { subject, date } 로 변경
  const { subject, date } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem } = useAuth();

  const handleGoBack = () => {
    navigate(-1);
  };

  const renderContent = () => {
    // 2단계: 날짜 폴더 내부 (파일 목록)
    if (subject && date) {
      // 'etc.' 폴더에 대한 특별 처리
      if (subject === 'etc.') {
        return <div>기타 파일들을 여기에 표시합니다.</div>;
      }
      const files = fileSystem[subject]?.[date] || [];
      if (files.length === 0) {
        return <div className="empty-folder-message">업로드된 파일이 없습니다.</div>;
      }
      // 향후 파일 목록 렌더링 로직 (지금은 비어있음)
      return files.map((file: any, index: number) => (
        <div key={index} className="folder-item">
          <FiFileText />
          <span>{file.name}</span>
        </div>
      ));
    }
    
    // 1단계: 과목 폴더 내부 (날짜 폴더 목록)
    if (subject) {
      // 'etc.' 폴더에 대한 특별 처리
      if (subject === 'etc.') {
         return <div>날짜 정보가 없는 파일들이 여기에 표시됩니다.</div>;
      }
      const dates = fileSystem[subject] || {};
      const dateKeys = Object.keys(dates);

      if (dateKeys.length === 0) {
        return <div className="empty-folder-message">생성된 날짜 폴더가 없습니다.</div>;
      }

      return dateKeys.map(dateKey => (
        <Link to={`/files/${subject}/${dateKey}`} key={dateKey} className="folder-item">
          <FiFolder />
          <span>{dateKey}</span>
        </Link>
      ));
    }

    // 최상위: 모든 과목 폴더 + 'etc' 폴더
    const subjectFolders = Object.keys(fileSystem).map(subjectName => (
      <Link to={`/files/${subjectName}`} key={subjectName} className="folder-item">
        <FiFolder />
        <span>{subjectName}</span>
      </Link>
    ));

    // 'etc' 폴더는 항상 표시 (옵션)
    subjectFolders.push(
      <Link to="/files/etc." key="etc" className="folder-item">
        <FiFolder />
        <span>etc.</span>
      </Link>
    );
    
    return subjectFolders;
  };

  // Breadcrumbs 로직을 새로운 'date' 파라미터에 맞게 수정
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
