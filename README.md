# Workout Tracker API

JWT-secured REST API to manage workouts, schedule sessions, and view reports.
Built with Flask, SQLAlchemy, JWT, Alembic, and SQLite (Docker optional).

## Features
- User auth (signup/login/JWT)
- Workout CRUD with exercises (sets/reps/weight)
- Scheduling (per-workout schedules)
- Reports (overview, weekly, exercise progress, upcoming)
- Swagger UI (`/apidocs`) and a simple in-app Playground (`/ui`)
- Tests (pytest) and DB migrations (Flask-Migrate/Alembic)

## Tech
Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow, Flasgger, Gunicorn, SQLite.

## Prereqs
- Python 3.12+
- (Optional) Docker Desktop

---

## Quickstart (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create a local env file
cp .env.example .env   

# Use SQLite by default
export FLASK_APP="src.app:create_app"
unset DATABASE_URL            

# DB schema + seed
flask db upgrade
python seeds.py

# Run API
flask run --host 0.0.0.0 --port 5000