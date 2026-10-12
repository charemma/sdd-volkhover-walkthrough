"""TCP port probing for enum_ports (spec 001-enum-ports.md, Port Probing)."""

import asyncio
from collections.abc import Iterable
from contextlib import suppress

CONNECT_TIMEOUT_SECONDS = 1.0
MAX_CONCURRENT_PROBES = 100
LOCALHOST = "localhost"
LOCALHOST_ADDRESS = "127.0.0.1"


def probe_host(target: str) -> str:
    """Return the address to connect to for a target, without name resolution."""
    return LOCALHOST_ADDRESS if target == LOCALHOST else target


async def is_port_open(host: str, port: int, limit: asyncio.Semaphore) -> bool:
    async with limit:
        try:
            async with asyncio.timeout(CONNECT_TIMEOUT_SECONDS):
                _, writer = await asyncio.open_connection(host, port)
        except (OSError, TimeoutError):
            return False
        writer.close()
        with suppress(OSError):
            await writer.wait_closed()
        return True


async def find_open_ports(target: str, ports: Iterable[int]) -> list[int]:
    """Return the requested ports open on target, ascending and without duplicates."""
    host = probe_host(target)
    unique_ports = sorted(set(ports))
    limit = asyncio.Semaphore(MAX_CONCURRENT_PROBES)
    results = await asyncio.gather(*(is_port_open(host, port, limit) for port in unique_ports))
    return [port for port, is_open in zip(unique_ports, results, strict=True) if is_open]
