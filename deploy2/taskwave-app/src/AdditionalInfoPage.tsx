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
  const [dob, setDob] = useState(''); // YYYY-MM-DD
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
      // 1) 회원가입
      const tok = await fetchJSON<TokenPair>(EP.AUTH_SIGNUP, {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      });
      saveToken(tok.access_token);

      // 2) 추가 정보 저장(선택 스키마 서버와 맞춰 필요 키를 조정하세요)
      await fetchJSON(
        EP.ME,
        {
          method: 'PATCH',
          body: JSON.stringify({ school, dob }),
          headers: { ...authHeaders() },
        }
      );

      alert('회원가입이 완료되었습니다! 로그인 페이지로 이동합니다.');
      navigate('/login');
    } catch (err: any) {
      alert(err?.message ?? '회원가입 실패');
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
            <input id="name" value={name} onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)} required />
          </div>

          <div className="form-group">
            <label htmlFor="school">학교</label>
            <input id="school" value={school} onChange={(e: ChangeEvent<HTMLInputElement>) => setSchool(e.target.value)} />
          </div>

          <div className="form-group">
            <label htmlFor="dob">생년월일</label>
            <input id="dob" type="date" value={dob} onChange={(e: ChangeEvent<HTMLInputElement>) => setDob(e.target.value)} />
          </div>

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? '저장 중...' : '완료'}
          </button>
        </form>
      </div>
    </div>
  );
}
