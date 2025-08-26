import { useState, FormEvent } from 'react'; // FormEvent 타입을 임포트
import { useLocation, useNavigate } from 'react-router-dom';
import Header from './Header.tsx';
import './AdditionalInfoPage.css';

// location.state의 타입을 미리 정의
interface LocationState {
  email?: string;
  password?: string;
}

const AdditionalInfoPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // location.state의 타입을 우리가 정의한 LocationState라고 알려줌
  const { email = '', password = '' } = (location.state as LocationState) || {};

  const [name, setName] = useState('');
  const [school, setSchool] = useState('');
  const [dob, setDob] = useState('');

  // handleSubmit의 e 매개변수 타입을 FormEvent로 지정
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const finalSignupData = {
      email,
      password,
      name,
      school,
      dob,
    };
    console.log('최종 회원가입 정보:', finalSignupData);
    alert('회원가입이 완료되었습니다! 로그인 페이지로 이동합니다.');
    
    navigate('/login');
  };

  return (
    <div className="page-container">
      <Header />
      <main className="main-content">
        <div className="additional-info-box">
          <h1 className="additional-info-title">추가 정보 입력</h1>
          <p className="additional-info-subtitle">마지막 단계입니다. 프로필 정보를 입력해주세요.</p>
          <form onSubmit={handleSubmit} className="additional-info-form">
            <div className="form-group">
              <label htmlFor="name">성명</label>
              <input type="text" id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label htmlFor="school">학교</label>
              <input type="text" id="school" value={school} onChange={(e) => setSchool(e.target.value)} required />
            </div>
            <div className="form-group">
              <label htmlFor="dob">생년월일</label>
              <input type="text" id="dob" placeholder="예: 020314" value={dob} onChange={(e) => setDob(e.target.value)} required />
            </div>
            <button type="submit" className="submit-button">가입 완료</button>
          </form>
        </div>
      </main>
    </div>
  );
};

export default AdditionalInfoPage;