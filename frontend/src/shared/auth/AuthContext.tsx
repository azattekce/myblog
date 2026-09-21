import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { CSRF_HEADER, http, refreshAccessToken } from '../api/httpClient';
import { tokenStore } from '../api/tokenStore';

export interface CurrentUser {
  id: string;
  username: string;
  email: string;
  display_name: string;
  role: 'admin' | 'reader';
}

interface AuthState {
  user: CurrentUser | null;
  ready: boolean;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [ready, setReady] = useState(false);

  // Sayfa yenilendiğinde HttpOnly cookie üzerinden sessizce oturumu geri yükle
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await refreshAccessToken();
      if (token && !cancelled) {
        try {
          const me = await http.get<CurrentUser>('/identity/users/me');
          if (!cancelled) setUser(me.data);
        } catch {
          tokenStore.set(null);
        }
      }
      if (!cancelled) setReady(true);
    })();
    const unsubscribe = tokenStore.subscribe((t) => {
      if (!t) setUser(null);
    });
    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await http.post<{ access_token: string; user: CurrentUser }>('/identity/auth/login', {
      username,
      password,
    });
    tokenStore.set(res.data.access_token);
    setUser(res.data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await http.post('/identity/auth/logout', null, { headers: CSRF_HEADER });
    } finally {
      tokenStore.set(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, ready, isAdmin: user?.role === 'admin', login, logout }),
    [user, ready, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth, AuthProvider içinde kullanılmalı');
  return ctx;
}
