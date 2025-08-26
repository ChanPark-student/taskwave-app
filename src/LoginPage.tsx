import { useState, FormEvent, ChangeEvent } from 'react'; // ChangeEvent, FormEvent 타입 임포트
import { useNavigate } from 'react-router-dom';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import { useAuth } from './context/AuthContext.tsx';
import './LoginPage.css'; 

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const togglePasswordVisibility = () => {
    setIsPasswordVisible(!isPasswordVisible);
  };

  // e 매개변수의 타입을 FormEvent로 지정
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log('로그인 시도:', { email, password });
    
    login(); 
    navigate('/'); 
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="login-logo">Taskwave</h1>
        <h2 className="login-title">로그인</h2>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">이메일 입력</label>
            <input
              type="email"
              id="email"
              placeholder="email@example.com"
              value={email}
              // e 매개변수의 타입을 ChangeEvent로 지정
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <div className="label-wrapper">
              <label htmlFor="password">암호 입력</label>
              <a href="/forgot-password" className="forgot-password-link">
                암호를 잊으셨나요?
              </a>
            </div>
            <div className="password-input-wrapper">
              <input
                type={isPasswordVisible ? 'text' : 'password'}
                id="password"
                placeholder="암호 입력"
                value={password}
                // e 매개변수의 타입을 ChangeEvent로 지정
                onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                required
              />
              <span onClick={togglePasswordVisibility} className="password-toggle-icon">
                {isPasswordVisible ? <FiEyeOff /> : <FiEye />}
              </span>
            </div>
          </div>

          <button type="submit" className="submit-button">
            로그인
          </button>
        </form>
        
        <div className="footer-link-container">
          <p>Taskwave를 처음 사용하시나요? <span className="create-account-link" onClick={() => navigate('/signup')}>계정 만들기</span></p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;