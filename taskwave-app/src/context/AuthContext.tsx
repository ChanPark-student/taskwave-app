// src/context/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { fetchJSON, loadToken, clearToken } from '../lib/http';
import { EP } from '../lib/endpoints';

// --- 새로운 파일 시스템 타입 정의 ---
// Event 타입을 백엔드 스키마와 일치시킴
export interface EventInfo {
  id: string;
  title: string;
  event_type: 'exam' | 'assignment';
  date: string;
  warning_days: number;
}

export interface AppFileInfo {
  id: string;
  name: string;
  file_url: string;
  mime_type: string;
  size_bytes?: number;
}

export interface DateInfo {
  session_id: string | null;
  files: AppFileInfo[];
  events: EventInfo[]; // 단일 객체에서 리스트(배열)로 변경
}

export interface SubjectInfo {
  subject_id: string;
  dates: Record<string, DateInfo>;
}

export type FileSystemStructure = Record<string, SubjectInfo>;

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
  fileSystem: FileSystemStructure;
  updateProfile: (next: Partial<User>) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [fileSystem, setFileSystem] = useState<FileSystemStructure>({});

  const refreshMe = async () => {
    const token = loadToken();
    if (!token) {
      setUser(null);
      setFileSystem({});
      return;
    }
    try {
      const me = await fetchJSON<User>(EP.ME, { method: 'GET' });
      setUser(me);

      try {
        const structure = await fetchJSON<FileSystemStructure>(EP.FILES_STRUCTURE, { method: 'GET' });
        setFileSystem(structure);
      } catch (fsError) {
        console.error("Failed to fetch file system structure:", fsError);
        setFileSystem({});
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
      setUser(prev => (prev ? { ...prev, ...next } : prev));
    }
  };

  const logout = () => {
    clearToken();
    setUser(null);
    setFileSystem({});
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