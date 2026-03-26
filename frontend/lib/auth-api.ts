export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/auth';

// Token storage
let storedToken: string | null = null;

export function setAuthToken(token: string) {
  storedToken = token;
}

export function clearAuthToken() {
  storedToken = null;
}

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
  const response = await fetch(`${API_BASE_URL.replace('/auth', '')}/lessons/`);
  if (!response.ok) {
    throw new Error('Failed to fetch lessons');
  }
  return response.json();
}

export async function getLesson(slug: string): Promise<Lesson> {
  const response = await fetch(
    `${API_BASE_URL.replace('/auth', '')}/lessons/${slug}/`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch lesson');
  }
  return response.json();
}

// Attempt API
export async function createAttempt(exerciseId: number): Promise<Attempt> {
  const token = await getToken();
  const response = await fetch(
    `${API_BASE_URL.replace('/auth', '')}/attempts/`,
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
  const response = await fetch(
    `${API_BASE_URL.replace('/auth', '')}/attempts/${attemptId}/detail/`,
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
): Promise<Attempt> {
  const token = await getToken();
  const response = await fetch(
    `${API_BASE_URL.replace('/auth', '')}/attempts/${attemptId}/`,
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

  const response = await fetch(
    `${API_BASE_URL.replace('/auth', '')}/attempts/${attemptId}/verify/`,
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

// Helper function to get token from stored auth
async function getToken(): Promise<string> {
  if (!storedToken) {
    throw new Error('No authentication token available. Please log in first.');
  }
  return storedToken;
}
