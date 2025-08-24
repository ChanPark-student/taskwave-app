import { useState, FormEvent, ChangeEvent } from 'react'; // ChangeEvent, FormEvent 타입 임포트
import { useNavigate } from 'react-router-dom';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import './SignupPage.css';

const SignupPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const togglePasswordVisibility = () => {
    setIsPasswordVisible(!isPasswordVisible);
  };

  // e 매개변수의 타입을 FormEvent로 지정
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    navigate('/signup-info', { state: { email, password } });
  };

  return (
    <div className="signup-container">
      <div className="signup-box">
        <h1 className="signup-logo">Taskwave</h1>
        <h2 className="signup-title">회원가입</h2>

        <form onSubmit={handleSubmit} className="signup-form">
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
            <label htmlFor="password">암호 입력</label>
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
            회원가입
          </button>
        </form>
      </div>
    </div>
  );
};

export default SignupPage;