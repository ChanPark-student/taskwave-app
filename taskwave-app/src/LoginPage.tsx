// src/LoginPage.tsx
import './LoginPage.css';
import { useState, FormEvent, ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import { EP } from './lib/endpoints';
import { fetchJSON, saveToken } from './lib/http';
import { useAuth } from './context/AuthContext';

type TokenPair = { access_token: string; token_type: string };

const LoginPage = () => {
  const navigate = useNavigate();
  const { refreshMe } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  const togglePasswordVisibility = () => setIsPasswordVisible(v => !v);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    try {
      // 1) 로그인 (토큰 불필요 → auth:false)
      const data = await fetchJSON<TokenPair>(EP.AUTH_LOGIN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      // 2) 토큰 저장
      saveToken(data.access_token);
      await refreshMe();
      // 3) 바로 검증 호출 (Authorization 자동 첨부)
      await fetchJSON(EP.ME, { method: 'GET' });

      // 4) 성공 시 홈으로
      navigate('/');
    } catch (err: any) {
      console.error('[login] error', err);
      alert(err?.message ?? '로그인 실패');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h2>로그인</h2>
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <div className="password-input-wrapper">
              <input
                id="password"
                type={isPasswordVisible ? 'text' : 'password'}
                placeholder="비밀번호"
                value={password}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                required
              />
              <span onClick={togglePasswordVisibility} className="password-toggle-icon">
                {isPasswordVisible ? <FiEyeOff /> : <FiEye />}
              </span>
            </div>
          </div>

          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? '로그인 중...' : '로그인'}
          </button>
          <p className="helper">
            계정이 없나요? <span onClick={() => navigate('/signup')} className="link">회원가입</span>
          </p>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
