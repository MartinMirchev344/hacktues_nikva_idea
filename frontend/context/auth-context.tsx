import {
  createContext,
  PropsWithChildren,
  useContext,
  useState,
} from 'react';
import type { AuthResponse } from '../lib/auth-api';
import { setAuthToken, clearAuthToken } from '../lib/auth-api';

type AuthState = AuthResponse | null;

type AuthContextValue = {
  auth: AuthState;
  setAuth: (value: AuthState) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [auth, setAuth] = useState<AuthState>(null);

  const handleSetAuth = (value: AuthState) => {
    setAuth(value);
    if (value?.token) {
      setAuthToken(value.token);
    } else {
      clearAuthToken();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        auth,
        setAuth: handleSetAuth,
        logout: () => {
          setAuth(null);
          clearAuthToken();
        },
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
