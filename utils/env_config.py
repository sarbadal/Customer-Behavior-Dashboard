import os
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parents[1]


def load_env_file(file_path: Path, override: bool = False) -> None:
    """Load key/value pairs from the selected env file before app startup."""

    if not file_path.exists():
        return

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        if override or key not in os.environ:
            os.environ[key] = value


def resolve_env_file(selected_env: Optional[str] = None) -> Path:
    """Pick env file path using explicit selector, ENV_FILE override, or APP_ENV."""

    if selected_env:
        normalized = selected_env.strip().lower()
        if normalized == "prod":
            return BASE_DIR / ".env.prod"
        if normalized == "dev":
            return BASE_DIR / ".env.dev"
        return Path(selected_env).expanduser()

    explicit_env_file = os.getenv("ENV_FILE")
    if explicit_env_file:
        return Path(explicit_env_file).expanduser()

    app_env = os.getenv("APP_ENV", "dev").strip().lower()
    if app_env == "prod":
        return BASE_DIR / ".env.prod"
    return BASE_DIR / ".env.dev"


def env_bool(name: str, default: bool = True) -> bool:
    """Read a boolean env var for runtime flags such as DEBUG."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int = 5000) -> int:
    """Read an integer env var for numeric settings such as PORT."""

    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
