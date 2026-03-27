# Mimical

mimical is a mobile-first sign language learning app built with Expo React Native and Django. It lets users sign in, browse lessons, practice signs, record attempts, and get model-assisted feedback for sign verification.

The project is split into:

- `frontend/`: Expo app using `expo-router`
- `backend/mimical/`: Django API, lesson data, and recognition services

## What It Does

- User registration and login with DRF token auth
- Lesson browsing and lesson detail pages
- Exercise attempts and progress tracking
- XP and streak progression
- Sign verification endpoints backed by the recognition service
- Seeded ASL beginner content, including alphabet lessons, greetings, numbers, colors, feelings, and more

## Tech Stack

- Frontend: Expo, React Native, TypeScript, Expo Router
- Backend: Django, Django REST Framework, SQLite
- Recognition: 

## Project Structure

```text
hacktues_nikva_idea/
|-- frontend/
|   |-- app/
|   |-- assets/
|   |-- components/
|   |-- constants/
|   |-- context/
|   `-- lib/
|-- backend/
|   |-- mimical/
|   |   |-- lessons/
|   |   |-- recognition/
|   |   |-- users/
|   |   |-- mimical/
|   |   `-- manage.py
|   `-- model_cache/
`-- README.md
```

## Prerequisites

Before running the project, make sure you have:

- Node.js 18+ and `npm`
- Python 3.11+ recommended
- A virtual environment for the Django backend
- Expo Go or an Android/iOS simulator if you want to run the mobile app

## Frontend Setup

From [frontend/package.json](/c:/Users/marti/OneDrive/Documents/GitHub/hacktues_nikva_idea/frontend/package.json):

```bash
cd frontend
npm install
```

Create or update `frontend/.env`:

```env
EXPO_PUBLIC_API_BASE_URL=http://YOUR_LOCAL_IP:8000/api/auth
```

Notes:

- The frontend expects the auth base URL, not the root API URL.
- The app derives lesson and attempt endpoints from that value automatically.
- For a physical phone, use your laptop's local IP instead of `localhost`.

Start the Expo app:

```bash
cd frontend
npm start
```

## Backend Setup

The Django app lives in `backend/mimical`.

```bash
cd backend/mimical
python -m venv .venv
```

Activate the virtual environment:

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies. This repository currently does not include a committed `requirements.txt` or `pyproject.toml`, so you will need to install the packages your environment uses manually.

At minimum, the codebase expects:

- `django`
- `djangorestframework`
- `python-dotenv`
- `opencv-python`
- `numpy`

Optional but supported:

- `corsheaders`
- `djangorestframework-simplejwt`
- `mediapipe`
- `torch`
- `huggingface_hub`

Then run:

```bash
python manage.py migrate
python manage.py seed
python manage.py runserver 0.0.0.0:8000
```

## Environment Notes

Backend settings are read from `backend/mimical/.env` when `python-dotenv` is installed.

Recognition-related settings supported by the backend include:

- `RECOGNITION_MODEL_REPO`
- `RECOGNITION_MODEL_VARIANT`
- `RECOGNITION_DATASET_REPO`
- `RECOGNITION_DATASET_LABELS_FILE`
- `RECOGNITION_LABELS_PATH`
- `RECOGNITION_CACHE_DIR`
- `RECOGNITION_SUPPORTED_LESSONS`
- `HF_TOKEN`
- `MEDIAPIPE_HOLISTIC_TASK_PATH`
- `MEDIAPIPE_HOLISTIC_TASK_URL`

If these are not set, the backend falls back to defaults defined in [settings.py](/c:/Users/marti/OneDrive/Documents/GitHub/hacktues_nikva_idea/backend/mimical/mimical/settings.py) and [services.py](/c:/Users/marti/OneDrive/Documents/GitHub/hacktues_nikva_idea/backend/mimical/recognition/services.py).

Email-related settings for login OTP and password reset codes:

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

Example `backend/mimical/.env` for real SMTP delivery:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Mimical <your-email@gmail.com>
```

Important: if `EMAIL_BACKEND` is not set, the backend uses Django's console email backend, which prints OTP codes in the server terminal instead of sending them to the user's inbox.

## API Overview

Main API routes are:

- Auth: `/api/auth/register/`, `/api/auth/login/`, `/api/auth/me/`, `/api/auth/me/streak/`, `/api/auth/leaderboard/`
- Lessons: `/api/lessons/`, `/api/lessons/<slug>/`
- Attempts: `/api/attempts/`, `/api/attempts/<id>/`, `/api/attempts/<id>/detail/`, `/api/attempts/<id>/verify/`
- User progress: `/api/me/attempts/`, `/api/me/progress/`
- Recognition health: `/api/recognition/health/`

Important: the current backend implementation uses DRF token authentication and returns a `token` on login/register. The older JWT examples in [API.md](/c:/Users/marti/OneDrive/Documents/GitHub/hacktues_nikva_idea/backend/mimical/API.md) do not fully match the app's current implementation.

## Seeding Lessons

Lesson content is defined in [seed.py](/c:/Users/marti/OneDrive/Documents/GitHub/hacktues_nikva_idea/backend/mimical/lessons/management/commands/seed.py).

To populate or refresh lessons:

```bash
cd backend/mimical
python manage.py seed
```

To clear all existing lessons first:

```bash
python manage.py seed --clear
```

## Development Flow

Recommended local workflow:

1. Start the Django backend on `0.0.0.0:8000`
2. Confirm `frontend/.env` points to the correct machine IP
3. Start the Expo frontend
4. Create an account in the app
5. Seed lessons if the home screen is empty

## Known Gaps

- No backend dependency lockfile is committed yet
- `API.md` is partially outdated compared with the real token-auth implementation
- Recognition features depend on optional heavy ML packages that may not be installed in every local environment

## License

This repository includes a [LICENSE](/c:/Users/marti/OneDrive/Documents/GitHub/hacktues_nikva_idea/LICENSE) file.
