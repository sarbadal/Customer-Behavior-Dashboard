# Customer Behavioral Insights Dashboard

A Flask-based analytics prototype for visualizing customer behavior with synthetic datasets loaded from SQLite.

The app provides:
- KPI cards for users, sessions, orders, revenue, and average time spent.
- Interactive charts for browsing categories, device mix, revenue trends, city activity, and traffic sources.
- Filters for region, date range, and trend granularity.
- A dedicated About page with KPI definitions and a data dictionary.

## Features

- Flask app factory architecture.
- Typed dashboard service layer with dataclasses.
- SQLite mode (default), MySQL mode, plus local CSV and Google Cloud Storage bucket modes.
- Optional GCP auth strategies:
	- Service account JSON key.
	- Application Default Credentials (ADC).
- Modular frontend assets:
	- Template partials and base layout.
	- Dashboard JavaScript split by feature and chart-level files.

## Tech Stack

- Python 3.x
- Flask 3.0.3
- Chart.js (CDN)
- Google Cloud Storage client library

## Project Structure

```text
customer-behavioral/
├─ app_factory.py
├─ main.py
├─ setting.py
├─ requirements.txt
├─ routes/
│  └─ dashboard_routes.py
├─ services/
│  └─ dashboard_service.py
├─ utils/
│  ├─ csv_loader.py
│  ├─ env_config.py
│  └─ parsers.py
├─ scripts/
│  └─ generate_dummy_data.py
├─ data/
│  ├─ browsing_history.csv
│  ├─ purchase_patterns.csv
│  └─ location_data.csv
├─ templates/
│  ├─ base.html
│  ├─ dashboard.html
│  ├─ about.html
│  └─ partials/
├─ static/
│  ├─ styles.css
│  ├─ logo.png
│  ├─ favicon.ico
│  └─ js/dashboard/
│     ├─ utils.js
│     ├─ filters.js
│     ├─ charts.js
│     ├─ init.js
│     └─ charts/
└─ gcp/
	 └─ cred_key.json  (optional, local JSON-key mode)
```

## Quick Start (Local)

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Generate synthetic data.
5. Migrate CSV data into SQLite.
6. Run the Flask app.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/generate_dummy_data.py
python3 scripts/migrate_csv_to_sqlite.py
python3 main.py
```

Open:
- Dashboard: http://127.0.0.1:5000/
- About page: http://127.0.0.1:5000/about

## Environment Configuration

The app loads environment variables from:
- `.env.dev` by default.
- `.env.prod` when `APP_ENV=prod`.
- A custom file when `ENV_FILE=/path/to/file` is set.

Common runtime env vars:
- `APP_ENV` (for env file selection)
- `ENV_FILE` (explicit env file path)
- `HOST` (default: `127.0.0.1`)
- `PORT` (default: `5000`)
- `DEBUG` (default: `true`)
- `STATIC_ASSET_BASE_URL` (optional CDN/static bucket URL)
- `GCS_STATIC_BUCKET` and `GCS_STATIC_PREFIX` (optional, used to auto-build static URL)
- `GCP_USE_JSON_KEY` (boolean; default: `true`)
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` (for `DATA_SOURCE=mysql`)
- `DB_AUTO_BOOTSTRAP_FROM_SQLITE` (default: `true`; when mysql is selected, creates missing tables and seeds from local SQLite)

Boolean values are parsed as true for: `1`, `true`, `yes`, `on`.

## Data Source Modes

Configured in `setting.py`:

- `DATA_SOURCE = "sqlite"` (default)
	- Reads from SQLite at `SQLITE_DB_FILE` (default: `data/customer_behavior.db`).
	- To refresh the DB from CSV files:

	```bash
	python3 scripts/migrate_csv_to_sqlite.py
	```

- `DATA_SOURCE = "mysql"`
	- Reads from a MySQL server using:
		- `MYSQL_HOST` (default: `127.0.0.1`)
		- `MYSQL_PORT` (default: `3306`)
		- `MYSQL_USER` (default: `root`)
		- `MYSQL_PASSWORD`
		- `MYSQL_DATABASE` (default: `customer_behavior`)
	- Optional:
		- `MYSQL_SSL_CA` for TLS CA certificate path
		- `MYSQL_TABLE_BROWSING_HISTORY`, `MYSQL_TABLE_PURCHASE_PATTERNS`, `MYSQL_TABLE_LOCATION_DATA`
		  to map custom table names.
		- `DB_AUTO_BOOTSTRAP_FROM_SQLITE=true` to auto-create missing MySQL tables and seed from
		  local `SQLITE_DB_FILE` at app startup.

- `DATA_SOURCE = "local"`
	- Reads from the local `data/` folder.

- `DATA_SOURCE = "gcp_bucket"`
	- Reads CSV files from a GCS bucket.
	- Required settings:
		- `GCP_PROJECT_ID`
		- `GCP_BUCKET_NAME`
		- `GCP_BUCKET_DATA_PREFIX`

### GCP Authentication Options

1. JSON key mode (typically local development)
	 - Set `GCP_USE_JSON_KEY=true`
	 - Ensure `GCP_CREDENTIALS_FILE` points to your service account JSON file.

2. ADC mode (recommended on Cloud Run / Cloud Functions in same project)
	 - Set `GCP_USE_JSON_KEY=false`
	 - Ensure runtime identity has storage read permissions.

## Synthetic Data Generation

Generate or refresh CSVs:

```bash
python3 scripts/generate_dummy_data.py
```

Refresh SQLite after regenerating CSVs:

```bash
python3 scripts/migrate_csv_to_sqlite.py
```

Current generator defaults:
- 1500 rows per dataset.
- Deterministic random seed for reproducibility.

## Routes

- `GET /`
	- Dashboard with filters and charts.

- `GET /about`
	- KPI definitions and data dictionary.

- `GET /health`
	- Basic app liveness check.

- `GET /health/data`
	- Data-source readiness check for sqlite/mysql/local/gcp_bucket.
	- Returns `200` when healthy and `503` when validation fails.

## Deployment Notes

- Serve static assets from GCS in production by setting either:
	- `STATIC_ASSET_BASE_URL=https://storage.googleapis.com/<bucket>/<prefix>`
	- or `GCS_STATIC_BUCKET=<bucket>` and optional `GCS_STATIC_PREFIX=<prefix>`
- For GCP bucket data access in production, prefer `GCP_USE_JSON_KEY=false` and ADC.
- Keep credentials out of version control.

## License

This project is licensed under the terms in the `LICENSE` file.
