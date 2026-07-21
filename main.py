import argparse
import os
from typing import Optional

from flask import Request
from werkzeug.wrappers import Response as WerkzeugResponse

from utils.env_config import env_bool, env_int, load_env_file, resolve_env_file


app = None


def _create_configured_app(env_selector: Optional[str] = None):
    env_file = resolve_env_file(env_selector)
    load_env_file(env_file, override=bool(env_selector))

    # Import after environment is loaded so setting.py picks the right values.
    from app_factory import create_app

    return create_app()


def entry_point(request: Request) -> WerkzeugResponse:
    """Cloud Function HTTP entry point that forwards to the Flask WSGI app."""
    global app
    if app is None:
        app = _create_configured_app()
    return WerkzeugResponse.from_app(app, request.environ)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Customer Behavioral dashboard locally.")
    parser.add_argument(
        "--env",
        default="",
        help="Environment selector: dev, prod, or absolute/relative path to an env file.",
    )
    args = parser.parse_args()

    app = _create_configured_app(args.env or None)
    host = os.getenv("HOST", "127.0.0.1")
    port = env_int("PORT", 5000)
    debug = env_bool("DEBUG", True)
    app.run(host=host, port=port, debug=debug)
