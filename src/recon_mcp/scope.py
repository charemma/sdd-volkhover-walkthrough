"""Scope determination for enum_ports (spec 001-enum-ports.md, Scope Restriction, Scope Sources)."""

import ipaddress
import os
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal

type IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
type IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network
type Target = IPAddress | Literal["localhost"]

LOCALHOST: Literal["localhost"] = "localhost"
SCOPE_FILE_ENV = "RECON_SCOPE_FILE"
DEFAULT_SCOPE_FILE_NAME = "scope.md"
IN_SCOPE_HEADING = "## In Scope"
SECTION_END_MAX_LEVEL = 2
SCOPE_FILE_ENCODING = "utf-8"

IPV4_LOOPBACK = ipaddress.IPv4Network("127.0.0.0/8")
IPV6_LOOPBACK = ipaddress.IPv6Address("::1")
IPV4_MAPPED_LOOPBACK = ipaddress.IPv6Network("::ffff:127.0.0.0/104")

HEADING_PATTERN = re.compile(r"^(#{1,6})(?:\s|$)")
LIST_ITEM_PATTERN = re.compile(r"^[-*+] (.*)$")


class ScopeFileError(Exception):
    """The scope file cannot be read or contains an invalid entry."""


def parse_target(raw: str) -> Target | None:
    """Return the target named by a request, or None if it is not a literal IP or `localhost`."""
    if raw == LOCALHOST:
        return LOCALHOST
    try:
        return ipaddress.ip_address(raw)
    except ValueError:
        return None


def is_loopback(target: Target) -> bool:
    if target == LOCALHOST:
        return True
    if isinstance(target, ipaddress.IPv4Address):
        return target in IPV4_LOOPBACK
    return target == IPV6_LOOPBACK or target in IPV4_MAPPED_LOOPBACK


def matches_entry(address: IPAddress, entry: IPNetwork) -> bool:
    return address.version == entry.version and address in entry


def is_in_scope(target: Target, entries: Iterable[IPNetwork]) -> bool:
    if is_loopback(target):
        return True
    if target == LOCALHOST:
        return False
    return any(matches_entry(target, entry) for entry in entries)


def scope_file_path() -> Path:
    configured = os.environ.get(SCOPE_FILE_ENV)
    if configured is not None:
        return Path(configured)
    return Path.cwd() / DEFAULT_SCOPE_FILE_NAME


def missing_configured_scope_file() -> Path | None:
    """Return the path named by RECON_SCOPE_FILE if it is set but does not exist."""
    configured = os.environ.get(SCOPE_FILE_ENV)
    if configured is None or Path(configured).exists():
        return None
    return Path(configured)


def heading_level(line: str) -> int | None:
    match = HEADING_PATTERN.match(line)
    return len(match.group(1)) if match else None


def in_scope_items(text: str) -> Iterator[str]:
    """Yield the raw list item texts under the `## In Scope` heading."""
    in_section = False
    for line in text.splitlines():
        level = heading_level(line)
        if level is not None and level <= SECTION_END_MAX_LEVEL:
            in_section = line.rstrip() == IN_SCOPE_HEADING
            continue
        if in_section and (item := LIST_ITEM_PATTERN.match(line)):
            yield item.group(1).strip()


def parse_entry(raw: str) -> IPNetwork:
    try:
        return ipaddress.ip_network(raw)
    except ValueError as error:
        raise ScopeFileError(f"Scope file entry '{raw}' is invalid.") from error


def parse_scope_text(text: str) -> list[IPNetwork]:
    return [parse_entry(item) for item in in_scope_items(text)]


def read_scope_entries(path: Path) -> list[IPNetwork]:
    """Return the entries of the scope file at path; a missing file contributes no entries."""
    try:
        text = path.read_text(encoding=SCOPE_FILE_ENCODING)
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as error:
        raise ScopeFileError(f"Scope file {path} cannot be read.") from error
    return parse_scope_text(text)


def load_scope_entries() -> list[IPNetwork]:
    return read_scope_entries(scope_file_path())
