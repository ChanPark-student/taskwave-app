// src/Header.tsx
import './Header.css';

import { useNavigate } from 'react-router-dom';
import { FiUser, FiFolder, FiLogOut } from 'react-icons/fi';
import { useAuth } from './context/AuthContext.tsx';

const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const goToMyPage = () => navigate('/mypage');
  const goToMyFiles = () => navigate('/files');
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

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
            <div className="header-icon" onClick={handleLogout} title="로그아웃">
              <FiLogOut />
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
