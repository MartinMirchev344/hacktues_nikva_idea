export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/auth';

type AuthPayload = {
  email: string;
  password: string;
  confirmPassword?: string;
};

async function request<T>(path: string, body: Record<string, string>) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      data?.email?.[0] ??
      data?.password?.[0] ??
      data?.detail ??
      'Something went wrong. Please try again.';
    throw new Error(message);
  }

  return data as T;
}

export type AuthResponse = {
  token: string;
  user: {
    id: number;
    username: string;
    email: string;
    xp: number;
    streak: number;
    avatar_url: string;
  };
};

export function login(payload: AuthPayload) {
  return request<AuthResponse>('/login/', {
    email: payload.email,
    password: payload.password,
  });
}

export function register(payload: AuthPayload) {
  return request<AuthResponse>('/register/', {
    email: payload.email,
    password: payload.password,
    password2: payload.confirmPassword ?? '',
  });
}
