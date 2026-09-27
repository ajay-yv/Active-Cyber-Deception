# Database Runbook

## 1. Initialize local databases

The backend defaults to local SQLite files for development:

- `real_healthcare.db`
- `synthetic_healthcare.db`
- `security_events.db`

Start the backend once and the tables will be created automatically.

## 2. Run Alembic migrations

From the `backend/` directory:

```powershell
python -m alembic -c alembic.ini upgrade head
```

If you are using a virtual environment, activate it first so `alembic` resolves from the project dependencies.

## 3. Verify the app

```powershell
python -m pytest backend/tests
```

## 4. Reset local dev data

Delete the three SQLite files and rerun the app or Alembic command.
