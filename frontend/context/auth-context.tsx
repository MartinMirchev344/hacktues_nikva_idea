import {
  createContext,
  PropsWithChildren,
  useContext,
  useState,
} from 'react';
import type { AuthResponse } from '../lib/auth-api';

type AuthState = AuthResponse | null;

type AuthContextValue = {
  auth: AuthState;
  setAuth: (value: AuthState) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [auth, setAuth] = useState<AuthState>(null);

  return (
    <AuthContext.Provider
      value={{
        auth,
        setAuth,
        logout: () => setAuth(null),
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
