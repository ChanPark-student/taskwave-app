// src/AdditionalInfoPage.tsx
import './AdditionalInfoPage.css';

import { useLocation, useNavigate } from 'react-router-dom';
import { useState, FormEvent, ChangeEvent } from 'react';
import { EP } from './lib/endpoints';
import { fetchJSON, saveToken, authHeaders } from './lib/http';

type TokenPair = { access_token?: string; token_type?: string };

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
    // 1) 회원가입: 반드시 JSON 본문 + Content-Type 지정
    const tok = await fetchJSON<TokenPair>(EP.AUTH_SIGNUP, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    });

    if (!tok?.access_token) {
      throw new Error('회원가입 응답에 토큰이 없습니다.');
    }

    // 2) 토큰 저장
    saveToken(tok.access_token);

    // 3) 추가정보 저장 (서버가 204를 줄 수 있으므로 autoJson=false)
    await fetchJSON(
      EP.ME,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders(),
        },
        body: JSON.stringify({
          school: school || undefined,
          birth: birth || undefined, // 서버 스키마가 YYYY-MM-DD 기대하는지 확인
        }),
      },
    );

    alert('회원가입이 완료되었습니다! 로그인 페이지로 이동합니다.');
    navigate('/login');
  } catch (err: any) {
    console.error('[signup/additional]', err);
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
            <input id="dob" type="date" value={birth} onChange={(e: ChangeEvent<HTMLInputElement>) => setBirth(e.target.value)} />
          </div>

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? '저장 중...' : '완료'}
          </button>
        </form>
      </div>
    </div>
  );
}
