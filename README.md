# Customer Behavioral Insights Dashboard

A Flask-based analytics prototype for visualizing customer behavior with synthetic CSV datasets.

The app provides:
- KPI cards for users, sessions, orders, revenue, and average time spent.
- Interactive charts for browsing categories, device mix, revenue trends, city activity, and traffic sources.
- Filters for region, date range, and trend granularity.
- A dedicated About page with KPI definitions and a data dictionary.

## Features

- Flask app factory architecture.
- Typed dashboard service layer with dataclasses.
- Local CSV mode and Google Cloud Storage bucket mode.
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
5. Run the Flask app.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/generate_dummy_data.py
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
- `GCP_USE_JSON_KEY` (boolean; default: `true`)

Boolean values are parsed as true for: `1`, `true`, `yes`, `on`.

## Data Source Modes

Configured in `setting.py`:

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

Current generator defaults:
- 1500 rows per dataset.
- Deterministic random seed for reproducibility.

## Routes

- `GET /`
	- Dashboard with filters and charts.

- `GET /about`
	- KPI definitions and data dictionary.

## Deployment Notes

- You can serve static assets from CDN/bucket by setting `STATIC_ASSET_BASE_URL`.
- For GCP bucket data access in production, prefer `GCP_USE_JSON_KEY=false` and ADC.
- Keep credentials out of version control.

## License

This project is licensed under the terms in the `LICENSE` file.
