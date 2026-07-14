import os

from app_factory import create_app
from utils.env_config import env_bool, env_int, load_env_file, resolve_env_file


load_env_file(resolve_env_file())
app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = env_int("PORT", 5000)
    debug = env_bool("DEBUG", True)
    app.run(host=host, port=port, debug=debug)
