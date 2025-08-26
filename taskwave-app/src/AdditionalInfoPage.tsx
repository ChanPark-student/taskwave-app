// src/AdditionalInfoPage.tsx
import './AdditionalInfoPage.css';

import { useLocation, useNavigate } from 'react-router-dom';
import { useState, FormEvent, ChangeEvent } from 'react';
import { EP } from './lib/endpoints';
import { fetchJSON, saveToken, authHeaders } from './lib/http';

type TokenPair = { access_token: string; token_type: string };

export default function AdditionalInfoPage() {
  const navigate = useNavigate();
  const location = useLocation() as any;
  const { email, password } = (location?.state ?? {}) as { email?: string; password?: string };

  const [name, setName] = useState('');
  const [school, setSchool] = useState('');
  const [birth, setBirth] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email || !password) {
      alert('이전 단계 정보가 없습니다. 처음부터 다시 진행해주세요.');
      navigate('/signup');
      return;
    }
    setLoading(true);
    try {
      // 1) 회원가입: 일부 서버는 201/204 또는 유저 객체만 주므로 응답 바디는 신경 쓰지 않음
      await fetchJSON<any>(EP.AUTH_SIGNUP, {
        method: 'POST',
        // 서버 스키마에 맞게 필요시 키 수정(name -> full_name 등)
        body: JSON.stringify({ email, password, name }),
      }, /*autoJson*/ false); // 바디가 없을 수도 있으므로 텍스트로 받아 버림

      // 2) 바로 로그인해서 토큰 획득
      const tok = await fetchJSON<TokenPair>(EP.AUTH_LOGIN, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      if (!tok?.access_token) {
        throw new Error('로그인 토큰을 받지 못했습니다.');
      }
      saveToken(tok.access_token);

      // 3) 추가 정보 저장 (서버의 필드명에 맞춰 키 조정)
      await fetchJSON(
        EP.ME,
        {
          method: 'PATCH',
          body: JSON.stringify({ school, birth }),
          headers: { ...authHeaders() },
        }
      );

      alert('회원가입이 완료되었습니다! 로그인되었습니다.');
      navigate('/'); // 또는 로그인 페이지로 보내려면 '/login'
    } catch (err: any) {
      console.error('[signup-info] error', err);
      const msg = err?.message || '회원가입/로그인 과정에서 오류가 발생했습니다.';
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h2>추가 정보 입력</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">이름</label>
            <input id="name" value={name} onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label htmlFor="school">학교</label>
            <input id="school" value={school} onChange={(e: ChangeEvent<HTMLInputElement>) => setSchool(e.target.value)} />
          </div>
          <div className="form-group">
            <label htmlFor="birth">생년월일</label>
            <input id="birth" placeholder="YYYY-MM-DD" value={birth} onChange={(e: ChangeEvent<HTMLInputElement>) => setBirth(e.target.value)} />
          </div>
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? '처리 중...' : '완료'}
          </button>
        </form>
      </div>
    </div>
  );
}
