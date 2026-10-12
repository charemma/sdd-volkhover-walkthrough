# Code Generation Instructions

This file states the instructions AI MUST follow when generating or regenerating a file of type `code`.

## Tech Stack

- Code MUST target Python 3.12.
- The HTTP API MUST be built with FastAPI.
- The HTTP server MUST be uvicorn, declared as a runtime dependency and started from the console script `recon-mcp` in `pyproject.toml`; do not use `fastapi run` or a separate launcher script.
- Dependencies and environments MUST be managed with uv; do not use pip, Poetry, or requirements files.
- Tests MUST be written with pytest.
- ruff MUST be declared as a dev dependency in `pyproject.toml` (uv `dev` dependency group); do not rely on a globally installed ruff.

## Style

- Logic MUST be written as plain module-level functions; do not use classes for behavior.
- Classes MAY be used only as data containers (pydantic models, dataclasses) or where FastAPI requires them.
- Code MUST carry type hints.
- Optional types MUST be written as `X | None`; do not use `Optional[X]` or `Union`.
- File paths MUST be handled with `pathlib`; do not use `os.path`.
- Collections SHOULD be built with comprehensions or generators; do not use append loops where one fits.
- Linting and formatting MUST use ruff, configured in `pyproject.toml`; do not use a separate `ruff.toml`.
- Generated code MUST pass `uv run ruff check` and `uv run ruff format --check`.

## Layout

- Application code MUST live in the single package `src/recon_mcp`.
- Tests MUST live in `tests` as `test_<module>.py` files, without an `__init__.py`.
- `pyproject.toml` and `uv.lock` MUST live at the project root.
- Each test SHOULD name the spec section it verifies in its docstring.

## Commands

- Project commands MUST be run through uv as `uv run pytest`, `uv run ruff check` and `uv run ruff format --check`; do not invoke the tools directly or from an activated virtual environment.

## Host Prerequisites

- Generated code and its build configuration MUST require only uv on the contributor's host; declare any other tool as a dev dependency in `pyproject.toml` instead.
