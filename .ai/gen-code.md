# Code Generation Instructions

This file states the instructions AI MUST follow when generating or regenerating a file of type `code`.

## Tech Stack

- Code MUST target Python 3.12.
- The HTTP API MUST be built with FastAPI.
- Dependencies and environments MUST be managed with uv; do not use pip, Poetry, or requirements files.
- Tests MUST be written with pytest.

## Style

- Logic MUST be written as plain module-level functions; do not use classes for behavior.
- Classes MAY be used only as data containers (pydantic models, dataclasses) or where FastAPI requires them.
- Code MUST carry type hints.
- Optional types MUST be written as `X | None`; do not use `Optional[X]` or `Union`.
- File paths MUST be handled with `pathlib`; do not use `os.path`.
- Collections SHOULD be built with comprehensions or generators; do not use append loops where one fits.
- Linting and formatting MUST use ruff, configured in `pyproject.toml`; do not use a separate `ruff.toml`.
- Generated code MUST pass `ruff check` and `ruff format --check`.

## Layout

- Application code MUST live in the single package `src/recon_mcp`.
- Tests MUST live in `tests` as `test_<module>.py` files, without an `__init__.py`.
- `pyproject.toml` and `uv.lock` MUST live at the project root.
- Each test SHOULD name the spec section it verifies in its docstring.

