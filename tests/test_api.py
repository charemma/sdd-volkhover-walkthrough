import socket
from collections.abc import Iterable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from recon_mcp import api, scope

LOOPBACK = "127.0.0.1"
IN_SCOPE_TARGET = "10.20.1.15"
OUT_OF_SCOPE_TARGET = "10.0.0.5"


@pytest.fixture(autouse=True)
def isolated_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(scope.SCOPE_FILE_ENV, raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


@pytest.fixture
def scan_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, list[int]]]:
    """Replace the scanner so no traffic leaves the host; record its calls."""
    calls: list[tuple[str, list[int]]] = []

    async def fake_find_open_ports(target: str, ports: Iterable[int]) -> list[int]:
        calls.append((target, list(ports)))
        return [22]

    monkeypatch.setattr(api.scanner, "find_open_ports", fake_find_open_ports)
    return calls


@pytest.fixture
def listening_port() -> Iterator[int]:
    with socket.create_server((LOOPBACK, 0)) as server:
        yield server.getsockname()[1]


def write_scope(tmp_path: Path, *entries: str) -> None:
    items = "".join(f"- {entry}\n" for entry in entries)
    (tmp_path / "scope.md").write_text(f"# Scope\n\n## In Scope\n\n{items}")


def error_code(response) -> str:
    return response.json()["error"]["code"]


def test_scan_of_loopback_reports_open_ports(client: TestClient, listening_port: int) -> None:
    """Interface / Successful Response: 200 with target and open_ports."""
    response = client.post("/scan", json={"target": LOOPBACK, "ports": [listening_port]})
    assert response.status_code == 200
    assert response.json() == {"target": LOOPBACK, "open_ports": [listening_port]}


def test_duplicate_ports_are_reported_once(client: TestClient, listening_port: int) -> None:
    """Input Validation: duplicate ports are allowed and checked once."""
    response = client.post(
        "/scan", json={"target": "localhost", "ports": [listening_port, listening_port]}
    )
    assert response.status_code == 200
    assert response.json() == {"target": "localhost", "open_ports": [listening_port]}


def test_target_in_scope_file_is_scanned(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Scope Restriction: a target matching a scope file entry is scanned."""
    write_scope(tmp_path, "10.20.0.0/24", IN_SCOPE_TARGET)
    response = client.post("/scan", json={"target": IN_SCOPE_TARGET, "ports": [22, 80]})
    assert response.status_code == 200
    assert response.json() == {"target": IN_SCOPE_TARGET, "open_ports": [22]}
    assert scan_calls == [(IN_SCOPE_TARGET, [22, 80])]


def test_scope_file_from_environment_is_used(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scan_calls: list[tuple[str, list[int]]],
) -> None:
    """Scope File: the scope file path is taken from RECON_SCOPE_FILE."""
    engagement = tmp_path / "engagement.md"
    engagement.write_text(f"## In Scope\n- {IN_SCOPE_TARGET}\n")
    monkeypatch.setenv(scope.SCOPE_FILE_ENV, str(engagement))
    response = client.post("/scan", json={"target": IN_SCOPE_TARGET, "ports": [22]})
    assert response.status_code == 200
    assert len(scan_calls) == 1


def test_target_not_in_scope_is_rejected_without_traffic(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Scope Restriction / Error Response: 403 target_not_allowed, no scan."""
    write_scope(tmp_path, IN_SCOPE_TARGET)
    response = client.post("/scan", json={"target": OUT_OF_SCOPE_TARGET, "ports": [22]})
    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "target_not_allowed",
        "message": f"Target {OUT_OF_SCOPE_TARGET} is not in scope.",
    }
    assert scan_calls == []


def test_without_scope_file_only_loopback_is_in_scope(
    client: TestClient, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Scope File: without a scope file only loopback targets are in scope."""
    response = client.post("/scan", json={"target": "0.0.0.0", "ports": [22]})
    assert response.status_code == 403
    assert error_code(response) == "target_not_allowed"
    assert scan_calls == []


def test_invalid_scope_file_entry_is_rejected(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Scope File / Error Response: 500 invalid_scope_file naming the entry, even for loopback."""
    write_scope(tmp_path, "scanme.example.com")
    response = client.post("/scan", json={"target": LOOPBACK, "ports": [22]})
    assert response.status_code == 500
    assert error_code(response) == "invalid_scope_file"
    assert "scanme.example.com" in response.json()["error"]["message"]
    assert scan_calls == []


def test_unreadable_scope_file_is_rejected(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Scope File: a scope file that cannot be read as UTF-8 is invalid_scope_file."""
    (tmp_path / "scope.md").write_bytes(b"\xff\xfe")
    response = client.post("/scan", json={"target": LOOPBACK, "ports": [22]})
    assert response.status_code == 500
    assert error_code(response) == "invalid_scope_file"
    assert scan_calls == []


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"[]",
        b'{"ports": [22]}',
        b'{"target": "127.0.0.1"}',
        b'{"target": 127, "ports": [22]}',
        b'{"target": "127.0.0.1", "ports": "22"}',
        b'{"target": "127.0.0.1", "ports": [true]}',
        b'{"target": "127.0.0.1", "ports": [22.5]}',
        b'{"target": "127.0.0.1", "ports": ["22"]}',
    ],
)
def test_malformed_body_is_invalid_request(
    client: TestClient, body: bytes, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Error Response / Input Validation: malformed JSON, missing or wrongly typed fields."""
    response = client.post("/scan", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert error_code(response) == "invalid_request"
    assert scan_calls == []


@pytest.mark.parametrize("target", ["example.com", "", "10.0.0.0/24"])
def test_non_literal_target_is_invalid_target(
    client: TestClient, target: str, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: target must be a literal IP address or localhost."""
    response = client.post("/scan", json={"target": target, "ports": [22]})
    assert response.status_code == 400
    assert error_code(response) == "invalid_target"
    assert scan_calls == []


@pytest.mark.parametrize("ports", [[], [0], [65536], [22, -1]])
def test_out_of_range_ports_are_invalid_ports(
    client: TestClient, ports: list[int], scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: ports must be non-empty and within 1-65535."""
    response = client.post("/scan", json={"target": LOOPBACK, "ports": ports})
    assert response.status_code == 400
    assert error_code(response) == "invalid_ports"
    assert scan_calls == []


def test_port_range_bounds_are_valid(
    client: TestClient, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: 1 and 65535 are valid ports."""
    response = client.post("/scan", json={"target": LOOPBACK, "ports": [1, 65535]})
    assert response.status_code == 200


def test_unknown_fields_are_ignored(
    client: TestClient, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: unknown fields in the request body are ignored."""
    response = client.post("/scan", json={"target": LOOPBACK, "ports": [22], "extra": 1})
    assert response.status_code == 200


def test_invalid_target_is_reported_before_scope(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: an invalid target is invalid_target, not target_not_allowed."""
    write_scope(tmp_path, "scanme.example.com")
    response = client.post("/scan", json={"target": "scanme.example.com", "ports": [22]})
    assert error_code(response) == "invalid_target"


def test_invalid_target_is_reported_before_invalid_ports(
    client: TestClient, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: error order puts invalid_target before invalid_ports."""
    response = client.post("/scan", json={"target": "example.com", "ports": []})
    assert error_code(response) == "invalid_target"


def test_invalid_ports_are_reported_before_invalid_scope_file(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: error order puts invalid_ports before invalid_scope_file."""
    write_scope(tmp_path, "not-an-ip")
    response = client.post("/scan", json={"target": LOOPBACK, "ports": [0]})
    assert error_code(response) == "invalid_ports"


def test_unknown_path_is_not_found(client: TestClient) -> None:
    """Error Response: a path that does not exist is 404 not_found."""
    response = client.post("/nope", json={"target": LOOPBACK, "ports": [22]})
    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "not_found",
        "message": "Path /nope does not exist.",
    }


def test_wrong_method_is_method_not_allowed(client: TestClient) -> None:
    """Error Response: a method the path does not accept is 405 method_not_allowed."""
    response = client.get("/scan")
    assert response.status_code == 405
    assert error_code(response) == "method_not_allowed"
    assert response.headers["allow"] == "POST"


def test_wrong_method_is_reported_before_body_validation(
    client: TestClient, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Error Response: method_not_allowed is detected before the body is examined."""
    response = client.put("/scan", content=b"not json")
    assert error_code(response) == "method_not_allowed"
    assert scan_calls == []


def test_invalid_scope_file_is_reported_before_target_not_allowed(
    client: TestClient, tmp_path: Path, scan_calls: list[tuple[str, list[int]]]
) -> None:
    """Input Validation: error order puts invalid_scope_file before target_not_allowed."""
    write_scope(tmp_path, "not-an-ip")
    response = client.post("/scan", json={"target": OUT_OF_SCOPE_TARGET, "ports": [22]})
    assert error_code(response) == "invalid_scope_file"
