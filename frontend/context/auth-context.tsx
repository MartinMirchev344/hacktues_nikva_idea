import {
  createContext,
  PropsWithChildren,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import type { AuthResponse } from '../lib/auth-api';
import { setAuthToken, clearAuthToken } from '../lib/auth-api';

type AuthState = AuthResponse | null;
const AUTH_STORAGE_KEY = 'unspoken.auth';

type AuthContextValue = {
  auth: AuthState;
  isHydrating: boolean;
  setAuth: (value: AuthState) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function canUseWebStorage() {
  return Platform.OS === 'web' && typeof window !== 'undefined' && !!window.localStorage;
}

async function readStoredAuth() {
  if (canUseWebStorage()) {
    return window.localStorage.getItem(AUTH_STORAGE_KEY);
  }

  if (typeof SecureStore.getItemAsync === 'function') {
    return SecureStore.getItemAsync(AUTH_STORAGE_KEY);
  }

  return null;
}

async function writeStoredAuth(value: AuthResponse) {
  const serialized = JSON.stringify(value);

  if (canUseWebStorage()) {
    window.localStorage.setItem(AUTH_STORAGE_KEY, serialized);
    return;
  }

  if (typeof SecureStore.setItemAsync === 'function') {
    await SecureStore.setItemAsync(AUTH_STORAGE_KEY, serialized);
  }
}

async function clearStoredAuth() {
  if (canUseWebStorage()) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }

  if (typeof SecureStore.deleteItemAsync === 'function') {
    await SecureStore.deleteItemAsync(AUTH_STORAGE_KEY);
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [auth, setAuth] = useState<AuthState>(null);
  const [isHydrating, setIsHydrating] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const restoreAuth = async () => {
      try {
        const storedAuth = await readStoredAuth();
        if (!storedAuth) {
          return;
        }

        const parsedAuth = JSON.parse(storedAuth) as AuthResponse;
        if (parsedAuth?.token) {
          setAuthToken(parsedAuth.token);
        }

        if (isMounted) {
          setAuth(parsedAuth);
        }
      } catch {
        await clearStoredAuth();
        clearAuthToken();
      } finally {
        if (isMounted) {
          setIsHydrating(false);
        }
      }
    };

    restoreAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSetAuth = (value: AuthState) => {
    setAuth(value);
    setIsHydrating(false);

    void (async () => {
      if (value?.token) {
        setAuthToken(value.token);
        await writeStoredAuth(value);
      } else {
        clearAuthToken();
        await clearStoredAuth();
      }
    })();
  };

  return (
    <AuthContext.Provider
      value={{
        auth,
        isHydrating,
        setAuth: handleSetAuth,
        logout: () => {
          handleSetAuth(null);
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
