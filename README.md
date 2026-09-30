# Tobi — one AI, many minds
Multi-mode AI workspace. React (Vite, custom CSS) + FastAPI + SQLAlchemy/Alembic + Neon PostgreSQL + Gemini + Google Sign-In.

## Setup
1. **Neon**: create a project, copy the connection string into `DATABASE_URL` (`postgresql+psycopg://...?sslmode=require`).
2. **Gemini**: get a key at aistudio.google.com -> `GEMINI_API_KEY`.
3. **Google OAuth**: Cloud Console -> Credentials -> OAuth client (Web). Add `http://localhost:5173` as an Authorized JavaScript origin. Put the Client ID in `GOOGLE_CLIENT_ID` and in `frontend/.env` as `VITE_GOOGLE_CLIENT_ID`.
4. `cp .env.example .env` and fill it in.
5. Backend:
```
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic revision --autogenerate -m init && alembic upgrade head
uvicorn app.main:app --reload
```
6. Frontend: `cd frontend && npm install && npm run dev` (Vite proxies `/api` to :8000, so cookies stay same-origin).

## Security notes
Gemini key, DB URL and session secret stay server-side. Google ID tokens are verified server-side (signature, audience, verified email). Sessions are signed HttpOnly SameSite=Lax cookies. Every conversation/message/custom-mode query is ownership-checked. For production: serve over HTTPS, set `COOKIE_SECURE=true`, set `FRONTEND_URL`, and put the API behind the same origin as the frontend.

## Layout
`backend/app/` — `modes.py` (28 modes), `gemini_service.py`, `auth.py`, `models.py`, `main.py` (routes). `frontend/src/` — `App.jsx`, `api.js`, `styles.css`.

## Known gaps
Not yet implemented: edit-message, rate limiting, profile/settings pages (preferences API exists), attachments. Not run end-to-end — needs your credentials.
