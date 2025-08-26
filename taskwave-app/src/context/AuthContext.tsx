// src/context/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { fetchJSON, loadToken, clearToken } from '../lib/http';
import { EP } from '../lib/endpoints';

// 파일 트리 타입 (FileExplorerPage 사용 패턴과 일치)
export type DayItem = { name: string };
export type FileSystemTree = Record<string, { weeks: Record<string, DayItem[]> }>;

export type User = {
  id: string;
  email: string;
  name?: string;
  school?: string;
  // MyPage.tsx에서 참조하는 경우가 있어 선택 필드로 제공
  dob?: string;
  birth?: string;
};

export type AuthContextType = {
  user: User | null;
  refreshMe: () => Promise<void>;
  logout: () => void;

  // FileExplorerPage에서 fileSystem[subject]로 조회하므로 객체 트리 제공
  fileSystem: FileSystemTree;

  // MyPage.tsx에서 사용하는 경우가 있어 기본(stub) 제공
  updateProfile: (next: Partial<User>) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [fileSystem, setFileSystem] = useState<FileSystemTree>({});

  const refreshMe = async () => {
    const token = loadToken();
    if (!token) { setUser(null); return; }
    try {
      const me = await fetchJSON<User>(EP.ME, { method: 'GET' }); // Authorization은 fetchJSON 내부에서 처리된다고 가정
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
    }
  };

  // (선택) 파일 트리 초기화 — 실제 API가 있다면 여기에 붙이면 됨
  // 예: const tree = await fetchJSON<FileSystemTree>(EP.FILES, { method: 'GET' });
  useEffect(() => {
    void refreshMe();

    // 데모/초기 렌더용 더미 데이터 (원하면 제거 가능)
    // setFileSystem({
    //   math: { weeks: { '1주차': [{ name: '2025-03-03' }], '2주차': [{ name: '2025-03-10' }] } },
    //   physics: { weeks: { '1주차': [{ name: '2025-03-04' }] } },
    // });
  }, []);

  const updateProfile = async (next: Partial<User>) => {
    try {
      await fetchJSON<User>(EP.ME, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      });
      await refreshMe();
    } catch {
      setUser((prev) => (prev ? { ...prev, ...next } : prev));
    }
  };

  const logout = () => { clearToken(); setUser(null); };

  return (
    <AuthContext.Provider value={{ user, refreshMe, logout, fileSystem, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
