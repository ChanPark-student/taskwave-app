import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth, FileInfo } from './context/AuthContext.tsx';
import Header from './Header.tsx';
import { FiFolder, FiFileText, FiArrowLeft, FiUpload, FiChevronLeft, FiChevronRight, FiTrash2 } from 'react-icons/fi';
import './FileExplorerPage.css';
import { useRef, useState, ChangeEvent, useMemo } from 'react';
import { EP } from './lib/endpoints';
import { fetchJSON } from './lib/http';

// --- Calendar-related Helper Functions ---
const getDaysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
const getFirstDayOfMonth = (year: number, month: number) => new Date(year, month, 1).getDay(); // 0=Sun, 1=Mon

const CalendarView = ({ subjectName, dates }: { subjectName: string, dates: Record<string, any> }) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const scheduledDates = useMemo(() => new Set(Object.keys(dates)), [dates]);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); // 0-11

  const daysInMonth = getDaysInMonth(year, month);
  let firstDay = getFirstDayOfMonth(year, month);
  firstDay = firstDay === 0 ? 6 : firstDay - 1; // 0=Mon, 6=Sun

  const calendarDays = Array.from({ length: firstDay }, (_, i) => <div key={`empty-${i}`} className="calendar-day empty"></div>);
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const hasSchedule = scheduledDates.has(dateStr);
    const hasFiles = hasSchedule && dates[dateStr]?.files?.length > 0;

    let dayClassName = 'calendar-day';
    if (hasSchedule) {
      dayClassName += ' has-schedule';
      dayClassName += hasFiles ? ' has-files' : ' no-files';
    }

    calendarDays.push(
      hasSchedule ? (
        <Link to={`/files/${subjectName}/${dateStr}`} key={dateStr} className={dayClassName}>
          {day}
        </Link>
      ) : (
        <div key={dateStr} className={dayClassName}>
          {day}
        </div>
      )
    );
  }

  const goToPreviousMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const goToNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <button onClick={goToPreviousMonth}><FiChevronLeft /></button>
        <h2>{year}년 {month + 1}월</h2>
        <button onClick={goToNextMonth}><FiChevronRight /></button>
      </div>
      <div className="calendar-grid">
        <div className="day-name">월</div>
        <div className="day-name">화</div>
        <div className="day-name">수</div>
        <div className="day-name">목</div>
        <div className="day-name">금</div>
        <div className="day-name">토</div>
        <div className="day-name">일</div>
        {calendarDays}
      </div>
    </div>
  );
};

const FileExplorerPage = () => {
  const { subject, date } = useParams<{ subject: string; date: string }>();
  const navigate = useNavigate();
  const { fileSystem, refreshMe } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingFileId, setDeletingFileId] = useState<string | null>(null);

  const handleGoBack = () => navigate(-1);

  const handleUploadClick = () => fileInputRef.current?.click();

  const handleFileSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !subject || !date) return;

    const subjectData = fileSystem[subject];
    const dateData = subjectData?.dates?.[date];
    if (!subjectData || (!dateData && subject !== 'etc')) {
      setUploadError('업로드에 필요한 ID 정보를 찾을 수 없습니다.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject_id', subjectData.subject_id);
    if (dateData?.session_id && dateData.session_id !== 'N/A') {
      formData.append('session_id', dateData.session_id);
    }
    formData.append('name', file.name);

    try {
      await fetchJSON(EP.MATERIALS_UPLOAD, { method: 'POST', body: formData });
      await refreshMe();
    } catch (err) {
      console.error("File upload failed:", err);
      setUploadError('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: string, fileName: string) => {
    if (window.confirm(`정말로 '${fileName}' 파일을 삭제하시겠습니까?`)) {
      setDeletingFileId(fileId);
      try {
        await fetchJSON(EP.MATERIAL_DELETE(fileId), { method: 'DELETE' });
        await refreshMe();
      } catch (err) {
        alert('파일 삭제에 실패했습니다.');
        console.error('File deletion failed:', err);
      } finally {
        setDeletingFileId(null);
      }
    }
  };

  const renderContent = () => {
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
          {files.length === 0 && !isUploading ? (
            <div className="empty-folder-message">업로드된 파일이 없습니다.</div>
          ) : (
            files.map((file: FileInfo) => (
              <div key={file.id} className="file-item-container">
                <a href={file.file_url} target="_blank" rel="noopener noreferrer" className="file-link">
                  <FiFileText />
                  <span>{file.name}</span>
                </a>
                <button 
                  onClick={() => handleDeleteFile(file.id, file.name)}
                  disabled={deletingFileId === file.id}
                  className="delete-file-button"
                  title={`${file.name} 삭제`}
                >
                  {deletingFileId === file.id ? '...' : <FiTrash2 />}
                </button>
              </div>
            ))
          )}
        </>
      );
    } else if (subject) {
      const subjectData = fileSystem[subject];
      if (!subjectData) return <div className="empty-folder-message">과목 정보를 찾을 수 없습니다.</div>;
      return <CalendarView subjectName={subject} dates={subjectData.dates} />;
    } else {
      const subjectFolders = Object.keys(fileSystem)
        .filter(name => name.toLowerCase() !== 'etc')
        .map(subjectName => (
          <Link to={`/files/${subjectName}`} key={subjectName} className="folder-item">
            <FiFolder />
            <span>{subjectName}</span>
          </Link>
      ));

      if (fileSystem['etc']) {
        subjectFolders.push(
          <Link to="/files/etc" key="etc" className="folder-item">
            <FiFolder />
            <span>etc</span>
          </Link>
        );
      }

      return subjectFolders;
    }
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
          <div className="grid-container-calendar"> 
            {renderContent()}
          </div>
        </div>
      </main>
    </div>
  );
};

export default FileExplorerPage;