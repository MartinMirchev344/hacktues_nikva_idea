import Constants from 'expo-constants';
import { Platform } from 'react-native';

function normalizeBaseUrl(url: string) {
  return url.replace(/\/$/, '');
}

function isLoopbackUrl(url: string) {
  return /\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?(\/|$)/.test(url);
}

function resolveExpoHost() {
  const hostUri =
    Constants.expoConfig?.hostUri ??
    Constants.manifest2?.extra?.expoClient?.hostUri;

  return hostUri?.split(':')[0] ?? null;
}

function getDefaultApiBaseUrl() {
  const expoHost = resolveExpoHost();
  if (expoHost) {
    return `http://${expoHost}:8000/api/auth`;
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/auth';
  }

  return 'http://127.0.0.1:8000/api/auth';
}

function resolveApiBaseUrl() {
  const configuredBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
  const expoHost = resolveExpoHost();

  if (configuredBaseUrl) {
    const normalizedBaseUrl = normalizeBaseUrl(configuredBaseUrl);
    if (expoHost && Platform.OS !== 'web' && isLoopbackUrl(normalizedBaseUrl)) {
      return normalizedBaseUrl.replace(
        /\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?/,
        `//${expoHost}$2`
      );
    }
    return normalizedBaseUrl;
  }

  return getDefaultApiBaseUrl();
}

export const API_BASE_URL = resolveApiBaseUrl();
const API_ROOT_URL = API_BASE_URL.replace(/\/auth\/?$/, '');

function getNetworkErrorMessage() {
  return `Unable to reach the API at ${API_BASE_URL}. On a physical phone, make sure the backend is running on your laptop with: python manage.py runserver 0.0.0.0:8000`;
}

async function fetchWithNetworkHint(input: RequestInfo | URL, init?: RequestInit) {
  try {
    return await fetch(input, init);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(getNetworkErrorMessage());
    }
    throw error;
  }
}

// Token storage
let storedToken: string | null = null;

export function setAuthToken(token: string) {
  storedToken = token;
}

export function clearAuthToken() {
  storedToken = null;
}

type AuthPayload = {
  username?: string;
  email: string;
  password: string;
  confirmPassword?: string;
};

function getFirstErrorMessage(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) {
    return value;
  }

  if (Array.isArray(value)) {
    const firstString = value.find(
      (item): item is string => typeof item === 'string' && item.trim().length > 0
    );
    return firstString ?? null;
  }

  return null;
}

async function request<T>(path: string, body: Record<string, string>) {
  const response = await fetchWithNetworkHint(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      getFirstErrorMessage(data?.username) ??
      getFirstErrorMessage(data?.email) ??
      getFirstErrorMessage(data?.password) ??
      getFirstErrorMessage(data?.password2) ??
      getFirstErrorMessage(data?.non_field_errors) ??
      getFirstErrorMessage(data?.detail) ??
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

export type LoginResponse = { needs_otp: true; email: string } | AuthResponse;

export function login(payload: AuthPayload): Promise<LoginResponse> {
  return request<LoginResponse>('/login/', {
    email: payload.email,
    password: payload.password,
  });
}

export function register(payload: AuthPayload) {
  return request<AuthResponse>('/register/', {
    username: payload.username ?? '',
    email: payload.email,
    password: payload.password,
    password2: payload.confirmPassword ?? '',
  });
}

export function verifyLoginOtp(email: string, code: string): Promise<AuthResponse> {
  return request<AuthResponse>('/verify-otp/', { email, code, purpose: 'login' });
}

export function forgotPassword(email: string): Promise<{ detail: string }> {
  return request<{ detail: string }>('/forgot-password/', { email });
}

export function resetPassword(email: string, code: string, newPassword: string): Promise<AuthResponse> {
  return request<AuthResponse>('/reset-password/', { email, code, new_password: newPassword });
}

// Lesson and Exercise Types
export type Exercise = {
  id: number;
  title: string;
  exercise_type: 'gesture_practice' | 'movement_drill' | 'quiz';
  prompt: string;
  instructions: string;
  expected_sign: string;
  order: number;
  repetitions_target: number;
  passing_score: number;
  target_pose_data: Record<string, unknown>;
  target_motion_data: Record<string, unknown>;
  lesson: number;
  created_at: string;
  updated_at: string;
};

export type Lesson = {
  id: number;
  title: string;
  slug: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  sign_language: string;
  estimated_duration_minutes: number;
  is_published: boolean;
  exercises?: Exercise[];
  exercise_count?: number;
  created_at: string;
  updated_at: string;
};

export type Attempt = {
  id: number;
  user: number;
  exercise: Exercise;
  status: 'in_progress' | 'completed' | 'needs_review';
  score: number | null;
  accuracy_score: number | null;
  speed_score: number | null;
  handshape_score: number | null;
  detected_sign: string | null;
  coach_summary: string | null;
  feedback_items: unknown[] | null;
  tracking_data: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

// Lesson API
export async function getLessons(): Promise<Lesson[]> {
  const response = await fetchWithNetworkHint(`${API_ROOT_URL}/lessons/`);
  if (!response.ok) {
    throw new Error('Failed to fetch lessons');
  }
  return response.json();
}

export async function getLesson(slug: string): Promise<Lesson> {
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/lessons/${slug}/`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch lesson');
  }
  return response.json();
}

// Attempt API
export async function createAttempt(exerciseId: number): Promise<Attempt> {
  const token = await getToken();
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/attempts/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`,
      },
      body: JSON.stringify({ exercise: exerciseId }),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to create attempt');
  }
  return response.json();
}

export async function getAttemptDetail(attemptId: number): Promise<Attempt> {
  const token = await getToken();
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/attempts/${attemptId}/detail/`,
    {
      headers: {
        'Authorization': `Token ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch attempt details');
  }
  return response.json();
}

export async function submitAttempt(
  attemptId: number,
  data: {
    score?: number;
    accuracy_score?: number;
    speed_score?: number;
    handshape_score?: number;
    detected_sign?: string;
    coach_summary?: string;
    feedback_items?: unknown[];
    tracking_data?: Record<string, unknown>;
    status?: string;
    completed_at?: string;
  }
): Promise<Attempt & { total_xp?: number; streak?: number }> {
  const token = await getToken();
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/attempts/${attemptId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`,
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to submit attempt');
  }
  return response.json();
}

export type VerifyResult = {
  is_correct: boolean;
  confidence: number;
  detected_sign: string;
  accuracy_score: number;
  handshape_score: number;
  speed_score: number;
  coach_summary: string;
  feedback_items: string[];
  candidates?: Array<{
    sign: string;
    score: number;
    model_label?: string;
    class_index?: number;
  }>;
};

export async function verifySign(attemptId: number, videoUri: string): Promise<VerifyResult> {
  const token = await getToken();
  const formData = new FormData();
  formData.append('video', {
    uri: videoUri,
    name: 'sign.mp4',
    type: 'video/mp4',
  } as any);

  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/attempts/${attemptId}/verify/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error('Failed to verify sign');
  }
  return response.json();
}

export type AlphabetPrediction = {
  predicted_letter: string;
  confidence: number;
  top_predictions: Array<{ letter: string; confidence: number }>;
};

async function throwWithDetail(response: Response): Promise<never> {
  const data = await response.json().catch(() => ({}));
  throw new Error(data?.detail ?? 'Prediction failed');
}

export async function predictAlphabetPhoto(imageUri: string): Promise<AlphabetPrediction> {
  const token = await getToken();
  const formData = new FormData();
  formData.append('image', {
    uri: imageUri,
    name: 'photo.jpg',
    type: 'image/jpeg',
  } as any);
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/recognition/alphabet/predict/`,
    { method: 'POST', headers: { 'Authorization': `Token ${token}` }, body: formData }
  );
  if (!response.ok) return throwWithDetail(response);
  return response.json();
}

export async function predictAlphabetPhotoWeb(blob: Blob): Promise<AlphabetPrediction> {
  const token = await getToken();
  const formData = new FormData();
  formData.append('image', blob, 'photo.jpg');
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/recognition/alphabet/predict/`,
    { method: 'POST', headers: { 'Authorization': `Token ${token}` }, body: formData }
  );
  if (!response.ok) return throwWithDetail(response);
  return response.json();
}

export async function verifySignWeb(attemptId: number, blob: Blob): Promise<VerifyResult> {
  const token = await getToken();
  const formData = new FormData();
  formData.append('video', blob, 'sign.webm');
  const response = await fetchWithNetworkHint(
    `${API_ROOT_URL}/attempts/${attemptId}/verify/`,
    { method: 'POST', headers: { 'Authorization': `Token ${token}` }, body: formData }
  );
  if (!response.ok) throw new Error('Failed to verify sign');
  return response.json();
}

export async function getMyAttempts(): Promise<Attempt[]> {
  const token = await getToken();
  const response = await fetchWithNetworkHint(`${API_ROOT_URL}/me/attempts/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
  if (!response.ok) throw new Error('Failed to fetch attempts');
  return response.json();
}

// Helper function to get token from stored auth
async function getToken(): Promise<string> {
  if (!storedToken) {
    throw new Error('No authentication token available. Please log in first.');
  }
  return storedToken;
}
