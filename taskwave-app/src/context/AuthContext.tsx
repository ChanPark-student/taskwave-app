// src/context/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { fetchJSON, loadToken, clearToken } from '../lib/http';
import { EP } from '../lib/endpoints';

// 새로운 파일 시스템 구조에 맞는 타입 정의
// 예: { "과목 A": { "2025-09-02": [], "2025-09-09": [] } }
export type FileSystemStructure = Record<string, Record<string, any[]>>;

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
  fileSystem: FileSystemStructure; // 타입 변경
  updateProfile: (next: Partial<User>) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  // setFileSystem을 사용하도록 변경
  const [fileSystem, setFileSystem] = useState<FileSystemStructure>({});

  const refreshMe = async () => {
    const token = loadToken();
    if (!token) {
      setUser(null);
      setFileSystem({}); // 로그아웃 상태에서는 파일 시스템도 비움
      return;
    }
    try {
      // 1. 사용자 정보 가져오기
      const me = await fetchJSON<User>(EP.ME, { method: 'GET' });
      setUser(me);

      // 2. 파일 구조 정보 가져오기 (사용자 정보 로드 성공 후)
      try {
        const structure = await fetchJSON<FileSystemStructure>(EP.FILES_STRUCTURE, { method: 'GET' });
        setFileSystem(structure);
      } catch (fsError) {
        console.error("Failed to fetch file system structure:", fsError);
        setFileSystem({}); // 실패 시 비움
      }

    } catch {
      clearToken();
      setUser(null);
      setFileSystem({});
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
    setFileSystem({}); // 로그아웃 시 파일 시스템 비우기
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
