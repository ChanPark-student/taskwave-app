import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext.tsx';
import Header from './Header.tsx';
import { FiFolder, FiFileText, FiArrowLeft } from 'react-icons/fi';
import './FileExplorerPage.css';

// map 함수 안에서 사용할 dayItem 객체의 타입을 정의
interface DayItem {
  name: string;
}

const FileExplorerPage = () => {
  const { subject, week, day } = useParams();
  const navigate = useNavigate();
  const { fileSystem } = useAuth();

  const handleGoBack = () => {
    navigate(-1);
  };

  const renderContent = () => {
    // 3단계: 날짜 폴더
    if (subject && week && day) {
      if (subject === 'etc.') {
        return <div>기타 파일들을 여기에 표시합니다.</div>;
      }
      return (
        <>
          <div className="folder-item" onClick={() => alert('1장 내용 보기')}>
            <FiFileText />
            <span>제 1장</span>
          </div>
          <div className="folder-item" onClick={() => alert('2장 내용 보기')}>
            <FiFileText />
            <span>제 2장</span>
          </div>
        </>
      );
    }
    
    // 2단계: 주차별 폴더
    if (subject && week) {
      const days = fileSystem[subject]?.weeks?.[week] || [];
      return days.map((dayItem: DayItem) => (
        <Link to={`/files/${subject}/${week}/${dayItem.name}`} key={dayItem.name} className="folder-item">
          <FiFolder />
          <span>{dayItem.name}</span>
        </Link>
      ));
    }

    // 1단계: 과목별 폴더
    if (subject) {
      if (subject === 'etc.') {
         return <div>날짜 정보가 없는 파일들이 여기에 표시됩니다.</div>;
      }
      const weeks = fileSystem[subject]?.weeks || {};
      return Object.keys(weeks).map(weekKey => (
        <Link to={`/files/${subject}/${weekKey}`} key={weekKey} className="folder-item">
          <FiFolder />
          <span>{weekKey}</span>
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

    subjectFolders.push(
      <Link to="/files/etc." key="etc" className="folder-item">
        <FiFolder />
        <span>etc.</span>
      </Link>
    );
    
    return subjectFolders;
  };

  const Breadcrumbs = () => (
    <div className="breadcrumbs">
      <Link to="/files">내 파일</Link>
      {subject && <><span>&gt;</span><Link to={`/files/${subject}`}>{subject}</Link></>}
      {week && <><span>&gt;</span><Link to={`/files/${subject}/${week}`}>{week}</Link></>}
      {day && <><span>&gt;</span><span>{day}</span></>}
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