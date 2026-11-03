import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { authApi, TOKEN_KEY } from '../services/api';
import type { Role, User } from '../types';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  setUser: (user: User) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(localStorage.getItem(TOKEN_KEY)));
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUserState(null);
    setError(null);
  }, []);

  const refresh = useCallback(async () => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await authApi.me();
      setUserState(data);
    } catch {
      // Token rejected (expired/revoked) — drop the session.
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUserState(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // The axios interceptor fires this when any request comes back 401.
  useEffect(() => {
    const handler = () => logout();
    window.addEventListener('ms:unauthorized', handler);
    return () => window.removeEventListener('ms:unauthorized', handler);
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    const { data } = await authApi.login(email, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setToken(data.access_token);
    setUserState(data.user);
  }, []);

  const register = useCallback(async (email: string, name: string, password: string) => {
    setError(null);
    const { data } = await authApi.register(email, name, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setToken(data.access_token);
    setUserState(data.user);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      error,
      login,
      register,
      logout,
      refresh,
      setUser: setUserState,
      clearError: () => setError(null),
    }),
    [user, token, loading, error, login, register, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

export function hasRole(user: User | null, ...roles: Role[]): boolean {
  return Boolean(user && roles.includes(user.role));
}
