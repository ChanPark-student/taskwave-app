import { useState, useEffect, ChangeEvent } from 'react'; // ChangeEvent 타입 임포트
import { FiUploadCloud } from 'react-icons/fi';
import Header from './Header.tsx';
import { useAuth } from './context/AuthContext.tsx';
import './MyPage.css';

const MyPage = () => {
  const { user, updateProfile } = useAuth();

  // timetableImage의 타입을 string 또는 null로 지정
  const [timetableImage, setTimetableImage] = useState<string | null>(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  // tempProfile의 타입을 User 또는 null로 지정
  const [tempProfile, setTempProfile] = useState(user);

  useEffect(() => {
    setTempProfile(user);
  }, [user]);

  // e 매개변수의 타입을 ChangeEvent로 지정
  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>) => {
    // e.target.files가 null일 수 있으므로 확인
    const file = e.target.files?.[0];
    if (file) {
      setTimetableImage(URL.createObjectURL(file));
    }
  };

  const handleEditClick = () => {
    setTempProfile(user);
    setIsEditingProfile(true);
  };

  const handleSaveClick = () => {
    // tempProfile이 null이 아닐 때만 updateProfile 호출
    if (tempProfile) {
      updateProfile(tempProfile);
    }
    setIsEditingProfile(false);
  };

  const handleCancelClick = () => {
    setIsEditingProfile(false);
  };

  // e 매개변수의 타입을 ChangeEvent로 지정
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // tempProfile이 null일 경우를 대비하여 이전 값을 복사
    setTempProfile(prevProfile => prevProfile ? { ...prevProfile, [name]: value } : null);
  };

  if (!user) {
    return <div>로딩 중...</div>;
  }

  return (
    <div className="page-container">
      <Header />
      <main className="mypage-main-content">
        <h1 className="mypage-title">내 계정</h1>
        <div className="mypage-layout">
          <section className="profile-section">
            <div className="section-header">
              <h2>프로필</h2>
              {!isEditingProfile ? (
                <button onClick={handleEditClick} className="change-button">변경</button>
              ) : (
                <div className="edit-actions">
                  <button onClick={handleSaveClick} className="save-button">저장</button>
                  <button onClick={handleCancelClick} className="cancel-button">취소</button>
                </div>
              )}
            </div>

            {!isEditingProfile ? (
              <div className="profile-details">
                <p><strong>성명</strong><span>{user.name}</span></p>
                <p><strong>학교</strong><span>{user.school}</span></p>
                <p><strong>생년월일</strong><span>{user.birth}</span></p>
              </div>
            ) : (
              <div className="profile-edit-form">
                {/* tempProfile이 null일 수 있으므로, optional chaining (?.) 사용 */}
                <div className="form-row">
                  <label htmlFor="name">성명</label>
                  <input type="text" id="name" name="name" value={tempProfile?.name || ''} onChange={handleInputChange} />
                </div>
                <div className="form-row">
                  <label htmlFor="school">학교</label>
                  <input type="text" id="school" name="school" value={tempProfile?.school || ''} onChange={handleInputChange} />
                </div>
                <div className="form-row">
                  <label htmlFor="birth">생년월일</label>
                  <input type="text" id="birth" name="birth" value={tempProfile?.birth || ''} onChange={handleInputChange} />
                </div>
              </div>
            )}
          </section>

          <section className="timetable-section">
            {!timetableImage ? (
              <div className="timetable-upload-box">
                <h2>시간표 업로드</h2>
                <div className="upload-area">
                  <FiUploadCloud className="upload-icon" />
                  <p>시간표 파일을 업로드하면 자동으로 분석해 드립니다.</p>
                  <label htmlFor="timetable-upload" className="upload-button">시간표 파일 업로드</label>
                  <input id="timetable-upload" type="file" accept="image/*,.pdf" onChange={handleImageUpload} style={{ display: 'none' }} />
                  <button onClick={() => navigate('/add-schedule')} className="manual-add-button">수동으로 시간표 입력</button>
                </div>
              </div>
            ) : (
              <div className="timetable-display-box">
                <div className="section-header">
                  <h2>업로드된 시간표</h2>
                  <label htmlFor="timetable-modify" className="change-button">수정하기</label>
                  <input id="timetable-modify" type="file" accept="image/*,.pdf" onChange={handleImageUpload} style={{ display: 'none' }} />
                </div>
                <img src={timetableImage} alt="업로드된 시간표" />
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
};

export default MyPage;