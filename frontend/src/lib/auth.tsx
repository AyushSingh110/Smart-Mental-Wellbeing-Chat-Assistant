import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import { getCurrentUser, loginWithGoogle } from "./api";
import type { AuthUser } from "../types";

type AuthContextType = {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
  token: string | null;
  error: string | null;
  loginWithGoogleCredential: (credential: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  clearError: () => void;
};

const STORAGE_KEY = "smart-wellbeing-auth-token";
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshUserFromToken(currentToken: string) {
    const profile = await getCurrentUser(currentToken);
    setUser(profile);
  }

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      setIsLoading(false);
      return;
    }

    setToken(raw);
    void refreshUserFromToken(raw)
      .catch(() => {
        window.localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      isAuthenticated: Boolean(user && token),
      isLoading,
      user,
      token,
      error,
      loginWithGoogleCredential: async (credential: string) => {
        setError(null);
        setIsLoading(true);
        try {
          const auth = await loginWithGoogle(credential);
          window.localStorage.setItem(STORAGE_KEY, auth.access_token);
          setToken(auth.access_token);
          await refreshUserFromToken(auth.access_token);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Google sign-in failed");
          throw err;
        } finally {
          setIsLoading(false);
        }
      },
      logout: () => {
        setUser(null);
        setToken(null);
        setError(null);
        window.localStorage.removeItem(STORAGE_KEY);
      },
      refreshUser: async () => {
        if (!token) return;
        setIsLoading(true);
        try {
          await refreshUserFromToken(token);
        } finally {
          setIsLoading(false);
        }
      },
      clearError: () => setError(null),
    }),
    [error, isLoading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
