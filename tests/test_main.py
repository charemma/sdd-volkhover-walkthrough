from pathlib import Path

import pytest

from recon_mcp import main, scope


@pytest.fixture
def run_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(main.uvicorn, "run", lambda app, **options: calls.append(options))
    return calls


@pytest.fixture(autouse=True)
def isolated_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(scope.SCOPE_FILE_ENV, raising=False)
    monkeypatch.chdir(tmp_path)


def test_refuses_to_start_when_configured_scope_file_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, run_calls: list[dict[str, object]]
) -> None:
    """Scope File: RECON_SCOPE_FILE set to a missing file refuses start."""
    monkeypatch.setenv(scope.SCOPE_FILE_ENV, str(tmp_path / "absent.md"))
    with pytest.raises(SystemExit) as exit_info:
        main.main()
    assert exit_info.value.code != 0
    assert run_calls == []


def test_starts_with_existing_configured_scope_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, run_calls: list[dict[str, object]]
) -> None:
    """Scope File / Service Startup: an existing configured scope file allows start."""
    engagement = tmp_path / "engagement.md"
    engagement.write_text("## In Scope\n")
    monkeypatch.setenv(scope.SCOPE_FILE_ENV, str(engagement))
    main.main()
    assert len(run_calls) == 1


def test_starts_without_any_scope_file(run_calls: list[dict[str, object]]) -> None:
    """Scope File: without RECON_SCOPE_FILE and scope.md the service still starts."""
    main.main()
    assert len(run_calls) == 1


def test_listens_on_fixed_loopback_address(run_calls: list[dict[str, object]]) -> None:
    """Service Startup: the service listens on 127.0.0.1:8000."""
    main.main()
    assert run_calls == [{"host": "127.0.0.1", "port": 8000}]
