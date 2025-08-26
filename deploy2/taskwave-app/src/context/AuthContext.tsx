// src/context/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { fetchJSON, loadToken, clearToken } from '../lib/http';
import { EP } from '../lib/endpoints';

type User = { id: string; email: string; name?: string; school?: string; birth?: string };

type AuthContextType = {
  user: User | null;
  refreshMe: () => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  const refreshMe = async () => {
    const token = loadToken();
    if (!token) { setUser(null); return; }
    try {
      const me = await fetchJSON<User>(EP.ME, { method: 'GET' }); // Authorization 자동 첨부
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
    }
  };

  useEffect(() => { void refreshMe(); }, []);

  const logout = () => { clearToken(); setUser(null); };

  return (
    <AuthContext.Provider value={{ user, refreshMe, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
