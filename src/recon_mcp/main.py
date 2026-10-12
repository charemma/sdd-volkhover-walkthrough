"""Service startup of enum_ports (spec 001-enum-ports.md, Service Startup and Scope File)."""

import sys

import uvicorn

from recon_mcp import scope
from recon_mcp.api import app

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8000


def main() -> None:
    missing = scope.missing_configured_scope_file()
    if missing is not None:
        sys.exit(f"Scope file {missing} named by {scope.SCOPE_FILE_ENV} does not exist.")
    uvicorn.run(app, host=LISTEN_HOST, port=LISTEN_PORT)
