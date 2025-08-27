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
  // FileExplorerPage가 기대하는 모양을 유지
  const [fileSystem] = useState<FileSystemTree>({});

  const refreshMe = async () => {
    const token = loadToken();
    if (!token) {
      setUser(null);
      return;
    }
    try {
      // Authorization은 fetchJSON 내부에서 자동 첨부된다고 가정
      const me = await fetchJSON<User>(EP.ME, { method: 'GET' });
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
    }
  };

  useEffect(() => {
    void refreshMe();
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
      // 낙관적 업데이트 (실패해도 화면은 반영)
      setUser(prev => (prev ? { ...prev, ...next } : prev));
    }
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, refreshMe, logout, fileSystem, updateProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
