#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command and print it for easier debugging."""
    print("\n$", " ".join(cmd))
    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)

    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(
            f"Required command '{name}' was not found in PATH. Install Google Cloud SDK first."
        )


def bucket_exists(bucket_name: str, project_id: str) -> bool:
    result = run_cmd(
        [
            "gcloud",
            "storage",
            "buckets",
            "describe",
            f"gs://{bucket_name}",
            "--project",
            project_id,
        ],
        check=False,
    )
    return result.returncode == 0


def create_bucket_if_missing(bucket_name: str, project_id: str, bucket_location: str) -> None:
    if bucket_exists(bucket_name, project_id):
        print(f"Bucket already exists: gs://{bucket_name}")
        return

    print(f"Bucket not found. Creating: gs://{bucket_name}")
    run_cmd(
        [
            "gcloud",
            "storage",
            "buckets",
            "create",
            f"gs://{bucket_name}",
            "--project",
            project_id,
            "--location",
            bucket_location,
            "--uniform-bucket-level-access",
        ]
    )


def sync_static_files(static_dir: Path, bucket_name: str) -> None:
    if not static_dir.exists() or not static_dir.is_dir():
        raise RuntimeError(f"Static directory does not exist: {static_dir}")

    # rsync uploads and updates files in one command.
    run_cmd(
        [
            "gcloud",
            "storage",
            "rsync",
            "--recursive",
            str(static_dir),
            f"gs://{bucket_name}/static",
        ]
    )


def ensure_public_object_access(bucket_name: str, dry_run: bool = False) -> None:
    """Grant public read access to bucket objects for static hosting."""
    cmd = [
        "gcloud",
        "storage",
        "buckets",
        "add-iam-policy-binding",
        f"gs://{bucket_name}",
        "--member=allUsers",
        "--role=roles/storage.objectViewer",
    ]

    if dry_run:
        print("\n[DRY RUN]", " ".join(cmd))
        return

    run_cmd(cmd)


def load_env_file(env_file: Path) -> dict[str, str]:
    """Load KEY=VALUE pairs from a .env style file."""
    if not env_file.exists() or not env_file.is_file():
        raise RuntimeError(f"Env file does not exist: {env_file}")

    env_vars: dict[str, str] = {}
    lines = env_file.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            raise RuntimeError(f"Invalid env line {line_number} in {env_file}: '{raw_line}'")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            raise RuntimeError(f"Invalid env line {line_number} in {env_file}: empty key")

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        env_vars[key] = value

    return env_vars


def deploy_function(function_name: str, project_id: str, region: str, runtime: str, source_dir: Path, entry_point: str, env_vars: dict[str, str], allow_unauthenticated: bool) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as temp_env_file:
        json.dump(env_vars, temp_env_file)
        temp_env_path = Path(temp_env_file.name)

    cmd = [
        "gcloud",
        "functions",
        "deploy",
        function_name,
        "--gen2",
        "--project",
        project_id,
        "--region",
        region,
        "--runtime",
        runtime,
        "--source",
        str(source_dir),
        "--entry-point",
        entry_point,
        "--trigger-http",
        "--env-vars-file",
        str(temp_env_path),
        "--quiet",
    ]

    if allow_unauthenticated:
        cmd.append("--allow-unauthenticated")

    try:
        run_cmd(cmd)
    finally:
        temp_env_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deploy Flask app to Google Cloud Functions (Gen2), ensure bucket exists, "
            "and upload static files."
        )
    )
    parser.add_argument("--project-id", required=True, help="Google Cloud project ID")
    parser.add_argument("--region", default="us-central1", help="GCP region for deployment")
    parser.add_argument("--function-name", default="sales-dashboard", help="Cloud Function name")
    parser.add_argument("--entry-point", default="entry_point", help="Python function entry point")
    parser.add_argument("--runtime", default="python312", help="Cloud Functions runtime")
    parser.add_argument(
        "--bucket-name",
        required=True,
        help="GCS bucket name for static files (without gs://)",
    )
    parser.add_argument(
        "--bucket-location",
        default="US",
        help="Bucket location (for example: US, us-central1, asia-south1)",
    )
    parser.add_argument(
        "--static-dir",
        default="static",
        help="Local static files directory to upload",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Source directory passed to gcloud functions deploy",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env style file to load and pass as Cloud Function env vars",
    )
    parser.add_argument(
        "--allow-unauthenticated",
        action="store_true",
        help="Allow public HTTP access to the deployed function",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        require_command("gcloud")

        project_root = Path(__file__).resolve().parent
        static_dir = (project_root / args.static_dir).resolve()
        source_dir = (project_root / args.source_dir).resolve()
        env_file = (project_root / args.env_file).resolve()
        env_vars = load_env_file(env_file)
        env_vars.setdefault("FLASK_ENV", "production")
        env_vars.setdefault("APP_ENV", "production")
        env_vars["STATIC_BUCKET"] = args.bucket_name

        print("Starting production deployment workflow...")
        print(f"Project: {args.project_id}")
        print(f"Function: {args.function_name}")
        print(f"Region: {args.region}")
        print(f"Bucket: gs://{args.bucket_name}")
        print(f"Env file: {env_file}")

        create_bucket_if_missing(args.bucket_name, args.project_id, args.bucket_location)
        ensure_public_object_access(args.bucket_name)
        sync_static_files(static_dir, args.bucket_name)
        deploy_function(
            function_name=args.function_name,
            project_id=args.project_id,
            region=args.region,
            runtime=args.runtime,
            source_dir=source_dir,
            entry_point=args.entry_point,
            env_vars=env_vars,
            allow_unauthenticated=args.allow_unauthenticated,
        )

        print("\nDeployment completed in production mode.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"\nDeployment failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())