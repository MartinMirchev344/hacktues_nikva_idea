# UNSPOKEN API Documentation

Base URL: `http://<your-server>:8000`

All endpoints except **Register** and **Login** require a JWT token in the header:
```
Authorization: Bearer <access_token>
```

---

## Auth

### Register
`POST /api/auth/register/`

**Request:**
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepass123",
  "password2": "securepass123"
}
```

**Response `201`:**
```json
{
  "username": "john",
  "email": "john@example.com"
}
```

---

### Login
`POST /api/auth/login/`

**Request:**
```json
{
  "username": "john",
  "password": "securepass123"
}
```

**Response `200`:**
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

> Save the `access` token. Send it in every request as `Authorization: Bearer <access_token>`.
> Access tokens expire after **1 day**, refresh tokens after **30 days**.

---

### Refresh Token
`POST /api/auth/token/refresh/`

**Request:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response `200`:**
```json
{
  "access": "<new_access_token>"
}
```

---

### My Profile
`GET /api/auth/me/`

**Response `200`:**
```json
{
  "id": 1,
  "username": "john",
  "email": "john@example.com",
  "xp": 120,
  "streak": 3,
  "last_activity_date": "2026-03-26",
  "avatar_url": "",
  "date_joined": "2026-03-26T10:00:00Z"
}
```

**Update profile** `PATCH /api/auth/me/`
```json
{
  "avatar_url": "https://example.com/avatar.png"
}
```

---

### Leaderboard
`GET /api/auth/leaderboard/`

**Response `200`:** Array of top 20 users sorted by XP.
```json
[
  { "id": 1, "username": "john", "xp": 340, "streak": 7, ... },
  { "id": 2, "username": "jane", "xp": 280, "streak": 4, ... }
]
```

---

## Lessons

### List Lessons
`GET /api/lessons/`

**Query params (all optional):**
| Param | Example | Description |
|---|---|---|
| `sign_language` | `ASL` | Filter by sign language |
| `difficulty` | `beginner` | `beginner`, `intermediate`, `advanced` |
| `search` | `greet` | Search in title and description |
| `ordering` | `difficulty` | Sort by `difficulty`, `title`, `created_at` |

**Response `200`:**
```json
[
  {
    "id": 1,
    "title": "Greetings",
    "slug": "greetings",
    "description": "Learn the most essential signs for meeting and greeting people.",
    "difficulty": "beginner",
    "sign_language": "ASL",
    "estimated_duration_minutes": 5,
    "is_published": true,
    "exercise_count": 5
  }
]
```

---

### Lesson Detail
`GET /api/lessons/<slug>/`

Example: `GET /api/lessons/greetings/`

**Response `200`:**
```json
{
  "id": 1,
  "title": "Greetings",
  "slug": "greetings",
  "description": "Learn the most essential signs for meeting and greeting people.",
  "difficulty": "beginner",
  "sign_language": "ASL",
  "estimated_duration_minutes": 5,
  "is_published": true,
  "exercises": [
    {
      "id": 1,
      "lesson": 1,
      "title": "Hello",
      "exercise_type": "gesture_practice",
      "prompt": "Sign 'Hello'",
      "instructions": "Open your hand flat...",
      "expected_sign": "hello",
      "order": 1,
      "repetitions_target": 1,
      "passing_score": 70,
      "target_pose_data": {},
      "target_motion_data": {}
    }
  ],
  "created_at": "2026-03-26T10:00:00Z",
  "updated_at": "2026-03-26T10:00:00Z"
}
```

> `target_pose_data` and `target_motion_data` are JSON fields the hand-tracking team can populate with reference landmark data for each sign.

---

## Attempts

### Start an Attempt
`POST /api/attempts/`

Call this when the user begins an exercise.

**Request:**
```json
{
  "exercise": 1
}
```

**Response `201`:**
```json
{
  "id": 42,
  "exercise": 1,
  "status": "in_progress",
  "score": null,
  "accuracy_score": null,
  "speed_score": null,
  "handshape_score": null,
  "detected_sign": "",
  "coach_summary": "",
  "feedback_items": [],
  "tracking_data": {},
  "completed_at": null
}
```

> Save the `id` — you will need it to submit results.

---

### Submit Hand-Tracking Results ⭐
`PATCH /api/attempts/<id>/`

**This is the main endpoint for the hand-tracking module.**

Call this when the user finishes performing a sign and the tracking module has results.

**Request:**
```json
{
  "status": "completed",
  "accuracy_score": 87.50,
  "handshape_score": 91.00,
  "speed_score": 78.00,
  "detected_sign": "hello",
  "coach_summary": "Good form! Your fingers were well extended. Try to be a bit faster.",
  "feedback_items": [
    "Extend fingers more consistently",
    "Speed up the outward wave"
  ],
  "tracking_data": {
    "landmarks": [ ... ],
    "confidence": 0.92,
    "frames_analyzed": 30
  },
  "completed_at": "2026-03-26T12:00:00Z"
}
```

**Field reference:**

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | string | yes | Set to `"completed"` to trigger scoring |
| `accuracy_score` | float 0–100 | no | Overall sign accuracy from hand tracker |
| `handshape_score` | float 0–100 | no | How correct the hand shape was |
| `speed_score` | float 0–100 | no | How well-timed/paced the movement was |
| `detected_sign` | string | no | What sign the model thinks was performed |
| `coach_summary` | string | no | Human-readable feedback sentence |
| `feedback_items` | array of strings | no | Specific tips to improve |
| `tracking_data` | object | no | Raw landmark / confidence data (any shape) |
| `completed_at` | ISO datetime | no | When the attempt was finished |

**Response `200`:**
```json
{
  "id": 42,
  "exercise": 1,
  "status": "completed",
  "score": 85.50,
  "accuracy_score": 87.50,
  "handshape_score": 91.00,
  "speed_score": 78.00,
  "detected_sign": "hello",
  "coach_summary": "Good form! Try to be a bit faster.",
  "feedback_items": ["Speed up the outward wave"],
  "tracking_data": { ... },
  "completed_at": "2026-03-26T12:00:00Z",
  "total_xp": 140,
  "streak": 4
}
```

> `score` is computed automatically as the average of the provided subscores.
> `total_xp` and `streak` are returned so the UI can update immediately.
> The lesson is marked complete in the user's progress if `score >= passing_score` (default 70).

**Status values:**
| Value | Meaning |
|---|---|
| `in_progress` | Attempt started, not submitted yet |
| `completed` | Submitted with results — triggers scoring |
| `needs_review` | Use if the tracker was uncertain |

---

### My Attempts History
`GET /api/me/attempts/`

**Response `200`:** Array of all the user's attempts, newest first.

---

### My Lesson Progress
`GET /api/me/progress/`

**Response `200`:**
```json
[
  {
    "id": 1,
    "lesson": 1,
    "lesson_title": "Greetings",
    "lesson_slug": "greetings",
    "is_completed": true,
    "best_score": "91.00",
    "attempts_count": 3,
    "completed_at": "2026-03-26T12:05:00Z"
  }
]
```

---

## XP & Streak Logic

- **XP** is awarded when an attempt is submitted with `status: "completed"` and `score >= passing_score`
- Each exercise awards **20 XP** on pass
- **Streak** increments by 1 if the user completes at least one exercise each consecutive day
- Streak resets to 1 if a day is missed
- `total_xp` and `streak` are returned directly in the submit response so the app can show an animation immediately

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

| Status | Meaning |
|---|---|
| `400` | Bad request / validation error |
| `401` | Missing or invalid token |
| `403` | Authenticated but not allowed |
| `404` | Resource not found |
