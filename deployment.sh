#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./deployment.sh --project-id <project> --bucket-name <bucket> [options]

Required:
  --project-id <id>          Google Cloud project ID
  --bucket-name <name>       GCS bucket for static assets

Optional:
  --region <region>          Cloud Functions region (default: us-central1)
  --function-name <name>     Cloud Function name (default: sales-dashboard)
  --entry-point <name>       Python entry point (default: entry_point)
  --runtime <runtime>        Runtime (default: python312)
  --bucket-location <loc>    Bucket location (default: US)
  --static-dir <path>        Static directory (default: static)
  --source-dir <path>        Source directory (default: .)
  --env-file <path>          Env file path (default: .env.prod)
  --allow-unauthenticated    Allow public access
  -h, --help                 Show this help message

Example:
  ./deployment.sh \
    --project-id my-gcp-project \
    --bucket-name my-prod-static-bucket \
    --env-file .env.prod \
    --allow-unauthenticated
EOF
}

PROJECT_ID=""
BUCKET_NAME=""
REGION="us-central1"
FUNCTION_NAME="sales-dashboard"
ENTRY_POINT="entry_point"
RUNTIME="python312"
BUCKET_LOCATION="US"
STATIC_DIR="static"
SOURCE_DIR="."
ENV_FILE=".env.prod"
ALLOW_UNAUTHENTICATED="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --bucket-name)
      BUCKET_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --function-name)
      FUNCTION_NAME="$2"
      shift 2
      ;;
    --entry-point)
      ENTRY_POINT="$2"
      shift 2
      ;;
    --runtime)
      RUNTIME="$2"
      shift 2
      ;;
    --bucket-location)
      BUCKET_LOCATION="$2"
      shift 2
      ;;
    --static-dir)
      STATIC_DIR="$2"
      shift 2
      ;;
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --allow-unauthenticated)
      ALLOW_UNAUTHENTICATED="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$PROJECT_ID" || -z "$BUCKET_NAME" ]]; then
  echo "Error: --project-id and --bucket-name are required." >&2
  usage
  exit 1
fi

PYTHON_BIN="python3"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

cmd=(
  "$PYTHON_BIN" deployment.py
  --project-id "$PROJECT_ID"
  --region "$REGION"
  --function-name "$FUNCTION_NAME"
  --entry-point "$ENTRY_POINT"
  --runtime "$RUNTIME"
  --bucket-name "$BUCKET_NAME"
  --bucket-location "$BUCKET_LOCATION"
  --static-dir "$STATIC_DIR"
  --source-dir "$SOURCE_DIR"
  --env-file "$ENV_FILE"
)

if [[ "$ALLOW_UNAUTHENTICATED" == "true" ]]; then
  cmd+=(--allow-unauthenticated)
fi

"${cmd[@]}"