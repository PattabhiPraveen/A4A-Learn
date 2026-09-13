import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import {
  getAuthenticationExpiredEventName,
} from "../services/apiClient";

import {
  getCurrentUser,
  login as loginRequest,
} from "../services/authService";

import type {
  AuthUser,
} from "../types/auth";

const TOKEN_STORAGE_KEY =
  "a4a_access_token";

interface AuthContextValue {
  user: AuthUser | null;

  token: string | null;

  isAuthenticated: boolean;

  isLoading: boolean;

  login: (
    email: string,
    password: string,
  ) => Promise<AuthUser>;

  logout: () => void;
}

const AuthContext =
  createContext<AuthContextValue | undefined>(
    undefined,
  );

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [token, setToken] =
    useState<string | null>(() =>
      sessionStorage.getItem(
        TOKEN_STORAGE_KEY,
      ),
    );

  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const logout = useCallback(() => {
    sessionStorage.removeItem(
      TOKEN_STORAGE_KEY,
    );

    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    function handleAuthenticationExpired() {
      logout();
    }

    const eventName =
      getAuthenticationExpiredEventName();

    window.addEventListener(
      eventName,
      handleAuthenticationExpired,
    );

    return () => {
      window.removeEventListener(
        eventName,
        handleAuthenticationExpired,
      );
    };
  }, [logout]);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      if (!token) {
        if (!cancelled) {
          setUser(null);
          setIsLoading(false);
        }

        return;
      }

      try {
        const currentUser =
          await getCurrentUser(token);

        if (cancelled) {
          return;
        }

        if (!currentUser.is_active) {
          logout();
          return;
        }

        setUser(currentUser);
      } catch {
        if (!cancelled) {
          logout();
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    setIsLoading(true);

    void restoreSession();

    return () => {
      cancelled = true;
    };
  }, [token, logout]);

  const login = useCallback(
    async (
      email: string,
      password: string,
    ) => {
      const loginResult =
        await loginRequest({
          email,
          password,
        });

      if (!loginResult.access_token) {
        throw new Error(
          "Authentication succeeded but no access token was returned.",
        );
      }

      const currentUser =
        await getCurrentUser(
          loginResult.access_token,
        );

      if (!currentUser.is_active) {
        throw new Error(
          "This account is inactive.",
        );
      }

      sessionStorage.setItem(
        TOKEN_STORAGE_KEY,
        loginResult.access_token,
      );

      setToken(
        loginResult.access_token,
      );

      setUser(currentUser);

      return currentUser;
    },
    [],
  );

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated:
        Boolean(token && user),
      isLoading,
      login,
      logout,
    }),
    [
      user,
      token,
      isLoading,
      login,
      logout,
    ],
  );

  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}