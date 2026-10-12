import asyncio
import socket
from collections.abc import Iterator

import pytest

from recon_mcp import scanner

LOOPBACK = "127.0.0.1"


@pytest.fixture
def listening_ports() -> Iterator[list[int]]:
    sockets = [socket.create_server((LOOPBACK, 0)) for _ in range(2)]
    yield [sock.getsockname()[1] for sock in sockets]
    for sock in sockets:
        sock.close()


@pytest.fixture
def closed_port() -> int:
    with socket.socket() as sock:
        sock.bind((LOOPBACK, 0))
        return sock.getsockname()[1]


def test_only_open_ports_are_reported(listening_ports: list[int], closed_port: int) -> None:
    """Port Probing / Successful Response: closed ports are not included."""
    found = asyncio.run(scanner.find_open_ports(LOOPBACK, [*listening_ports, closed_port]))
    assert found == sorted(listening_ports)


def test_open_ports_are_ascending_without_duplicates(listening_ports: list[int]) -> None:
    """Successful Response / Input Validation: ascending, duplicates checked once."""
    requested = [*sorted(listening_ports, reverse=True), *listening_ports]
    found = asyncio.run(scanner.find_open_ports(LOOPBACK, requested))
    assert found == sorted(listening_ports)


def test_no_open_ports_yields_empty_list(closed_port: int) -> None:
    """Successful Response: an empty list means no requested port was open."""
    assert asyncio.run(scanner.find_open_ports(LOOPBACK, [closed_port])) == []


def test_localhost_is_probed_at_ipv4_loopback(listening_ports: list[int]) -> None:
    """Port Probing: localhost is probed at 127.0.0.1 without name resolution."""
    assert scanner.probe_host("localhost") == LOOPBACK
    assert asyncio.run(scanner.find_open_ports("localhost", listening_ports)) == sorted(
        listening_ports
    )


def test_connection_not_completing_in_time_counts_as_not_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Port Probing: a connection that does not complete within the timeout is not open."""

    async def never_connects(*_: object) -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(scanner, "CONNECT_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(scanner.asyncio, "open_connection", never_connects)
    assert asyncio.run(scanner.find_open_ports(LOOPBACK, [1, 2, 3])) == []


def test_connect_timeout_is_one_second() -> None:
    """Port Probing: a port is open if the connection completes within 1 second."""
    assert scanner.CONNECT_TIMEOUT_SECONDS == 1.0


def test_at_most_100_ports_are_probed_concurrently(monkeypatch: pytest.MonkeyPatch) -> None:
    """Port Probing: at most 100 ports are probed concurrently per request."""
    active = 0
    peak = 0

    async def slow_refusal(*_: object) -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        raise ConnectionRefusedError

    monkeypatch.setattr(scanner.asyncio, "open_connection", slow_refusal)
    asyncio.run(scanner.find_open_ports(LOOPBACK, range(1, 251)))
    assert peak == 100
