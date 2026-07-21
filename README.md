# Customer Behavioral Insights Dashboard

A streamlined Flask dashboard that reads data only from SQLite.

## Runtime scope

- Data source: SQLite only
- Dashboard data tables:
  - browsing_history
  - purchase_patterns
  - location_data
- Session extension:
  - Dashboard warning appears after a configurable delay
  - User click calls /heartbeat and updates Firestore last_access

## SQLite file

Preferred database path:

- data/customer_behaviour.db

You can also override the path with:

- SQLITE_DB_FILE=/absolute/path/to/db

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run the app.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Open:

- Dashboard: http://127.0.0.1:5000/
- About: http://127.0.0.1:5000/about
- Health: http://127.0.0.1:5000/health
- Data health: http://127.0.0.1:5000/health/data

## Environment variables

- HOST (default: 127.0.0.1)
- PORT (default: 5000)
- DEBUG (default: true)
- SQLITE_DB_FILE (optional SQLite override)
- SESSION_WARNING_DELAY_MINUTES (default: 30)
- FIRESTORE_DATABASE_ID (default: (default))
- FIRESTORE_CREDENTIALS_FILE (optional local JSON key path)
- GOOGLE_CLOUD_PROJECT (optional project id)

## License

See LICENSE.
