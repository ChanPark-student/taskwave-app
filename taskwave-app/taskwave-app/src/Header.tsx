import { useNavigate } from 'react-router-dom';
import { FiUser, FiFolder } from 'react-icons/fi';
import { useAuth } from './context/AuthContext.tsx';
import './Header.css';

const Header = () => {
  const navigate = useNavigate();
  // logout 함수는 현재 사용되지 않으므로, user만 가져오도록 수정
  const { user } = useAuth(); 

  const goToMyPage = () => navigate('/mypage');
  const goToMyFiles = () => navigate('/files');

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="logo" onClick={() => navigate('/')}>Taskwave</div>
        
        {user ? ( 
          <div className="profile-container">
            <div className="header-icon" onClick={goToMyFiles} title="내 파일">
              <FiFolder />
            </div>
            <div className="header-icon" onClick={goToMyPage} title="마이페이지">
              <FiUser />
            </div>
          </div>
        ) : (
          <div className="auth-buttons">
            <button onClick={() => navigate('/login')} className="btn-login">로그인</button>
            <button onClick={() => navigate('/signup')} className="btn-signup">회원가입</button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;