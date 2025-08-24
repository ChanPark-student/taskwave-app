# Taskwave Backend (FastAPI)

Clean FastAPI backend for the university learning MVP. Includes JWT auth, subjects/weeks/sessions hierarchy,
file uploads (local or S3), timetable upload placeholder, Alembic, and Docker.

## Quickstart (Docker)
```bash
cp .env.example .env
docker compose up --build
# API: http://localhost:8000/docs
# Media files served at: http://localhost:8000/media/<path>
```

## Local (no Docker)
- Create a PostgreSQL DB and set `DATABASE_URL` in `.env`
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Alembic
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Structure
```
app/
  core/ (config, security, dependencies)
  db/   (Base and Session)
  models/ (User, Subject/Week/Session, Material, TimetableUpload)
  schemas/ (Pydantic models)
  routers/ (auth, users, subjects, schedules, materials, uploads)
  services/ (storage, timetable)
  main.py
```
