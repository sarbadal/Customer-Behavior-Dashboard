import os

from flask import Request
from werkzeug.wrappers import Response as WerkzeugResponse

from app_factory import create_app
from utils.env_config import env_bool, env_int, load_env_file, resolve_env_file


load_env_file(resolve_env_file())
app = create_app()


def entry_point(request: Request) -> WerkzeugResponse:
    """Cloud Function HTTP entry point that forwards to the Flask WSGI app."""
    return WerkzeugResponse.from_app(app, request.environ)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = env_int("PORT", 5000)
    debug = env_bool("DEBUG", True)
    app.run(host=host, port=port, debug=debug)
