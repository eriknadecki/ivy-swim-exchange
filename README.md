# Ivy Swim Exchange

Kalshi-style prediction market for Ivy League swimming — order-book trading with
virtual currency on markets like "Will Princeton beat Harvard?" or "Who wins the
Ivy League Championship?", fed by manual live meet updates during the season.

See `backend/` for the FastAPI + matching engine service. A `frontend/` React app
will be added starting at milestone M6 (see the project plan).

## Backend setup

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy .env.example .env          # adjust if needed

cd ..
docker compose up -d            # starts Postgres

cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/health`

## Tests

```
cd backend
pytest -q
ruff check .
```
