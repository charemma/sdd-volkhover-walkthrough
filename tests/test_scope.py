import ipaddress
from pathlib import Path

import pytest

from recon_mcp import scope

SPEC_EXAMPLE = """# Scope: ACME internal test, 2026-10

Authorized by: J. Doe, ACME CISO. Window: 2026-10-12 to 2026-10-16.

## In Scope

- 10.20.0.0/24
- 10.20.1.15
"""


@pytest.fixture(autouse=True)
def isolated_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(scope.SCOPE_FILE_ENV, raising=False)
    monkeypatch.chdir(tmp_path)


def target(raw: str) -> scope.Target:
    parsed = scope.parse_target(raw)
    assert parsed is not None
    return parsed


@pytest.mark.parametrize(
    "raw", ["127.0.0.1", "127.255.255.254", "::1", "::ffff:127.0.0.1", "localhost"]
)
def test_loopback_targets_are_in_scope_without_entries(raw: str) -> None:
    """Scope Restriction / Loopback Targets."""
    assert scope.is_in_scope(target(raw), [])


@pytest.mark.parametrize("raw", ["0.0.0.0", "::", "10.0.0.5", "::ffff:10.0.0.5"])
def test_non_loopback_targets_are_not_in_scope_without_entries(raw: str) -> None:
    """Scope Restriction / Loopback Targets: 0.0.0.0 and :: are not loopback."""
    assert not scope.is_in_scope(target(raw), [])


@pytest.mark.parametrize("raw", ["10.0.0.5", "2001:db8::1", "localhost"])
def test_parse_target_accepts_literal_addresses_and_localhost(raw: str) -> None:
    """Input Validation: target is a literal IP address or localhost."""
    assert scope.parse_target(raw) is not None


@pytest.mark.parametrize(
    "raw", ["example.com", "", "10.0.0.0/24", "localhost.localdomain", "300.1.1.1"]
)
def test_parse_target_rejects_other_values(raw: str) -> None:
    """Input Validation: other hostnames and non-addresses are rejected."""
    assert scope.parse_target(raw) is None


def test_target_matches_single_address_and_range() -> None:
    """Scope Sources / Entries: same address or inside the range."""
    entries = scope.parse_scope_text(SPEC_EXAMPLE)
    assert scope.is_in_scope(target("10.20.1.15"), entries)
    assert scope.is_in_scope(target("10.20.0.200"), entries)
    assert not scope.is_in_scope(target("10.20.1.16"), entries)


def test_ipv6_entries_match() -> None:
    """Scope Sources / Entries: IPv6 addresses and ranges."""
    entries = [ipaddress.ip_network("2001:db8::/64")]
    assert scope.is_in_scope(target("2001:db8::42"), entries)
    assert not scope.is_in_scope(target("2001:db9::42"), entries)


def test_ipv4_mapped_target_does_not_match_ipv4_entry() -> None:
    """Scope Sources / Entries: IPv4-mapped targets do not match IPv4 entries."""
    entries = [ipaddress.ip_network("10.20.1.15")]
    assert not scope.is_in_scope(target("::ffff:10.20.1.15"), entries)


def test_ipv4_target_does_not_match_ipv4_mapped_entry() -> None:
    """Scope Sources / Entries: IPv4 targets do not match IPv4-mapped entries."""
    entries = [ipaddress.ip_network("::ffff:10.20.1.15")]
    assert not scope.is_in_scope(target("10.20.1.15"), entries)


def test_spec_example_yields_its_entries() -> None:
    """Scope File: entries are the list items under ## In Scope."""
    assert scope.parse_scope_text(SPEC_EXAMPLE) == [
        ipaddress.ip_network("10.20.0.0/24"),
        ipaddress.ip_network("10.20.1.15"),
    ]


def test_section_ends_at_next_level_two_heading() -> None:
    """Scope File: the section ends at the next heading of level 1 or 2."""
    text = "## In Scope\n\n- 10.0.0.1\n\n## Notes\n\n- not an entry\n"
    assert scope.parse_scope_text(text) == [ipaddress.ip_network("10.0.0.1")]


def test_section_ends_at_next_level_one_heading() -> None:
    """Scope File: the section ends at the next heading of level 1 or 2."""
    text = "## In Scope\n- 10.0.0.1\n# Appendix\n- not an entry\n"
    assert scope.parse_scope_text(text) == [ipaddress.ip_network("10.0.0.1")]


def test_lower_level_heading_does_not_end_section() -> None:
    """Scope File: only headings of level 1 or 2 end the section."""
    text = "## In Scope\n### Office\n- 10.0.0.1\n"
    assert scope.parse_scope_text(text) == [ipaddress.ip_network("10.0.0.1")]


def test_all_list_markers_and_whitespace_are_accepted() -> None:
    """Scope File: list items start with -, * or +; surrounding whitespace is ignored."""
    text = "## In Scope\n-   10.0.0.1  \n* 10.0.0.2\n+ 10.0.0.3\n"
    assert scope.parse_scope_text(text) == [
        ipaddress.ip_network(address) for address in ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
    ]


def test_free_text_is_ignored() -> None:
    """Scope File: everything except list items under ## In Scope is ignored."""
    text = "- 10.9.9.9\n## In Scope\nfree text 10.0.0.9\n- 10.0.0.1\n"
    assert scope.parse_scope_text(text) == [ipaddress.ip_network("10.0.0.1")]


@pytest.mark.parametrize("entry", ["scanme.example.com", "not-an-ip", "10.0.0.0/33"])
def test_invalid_entry_is_reported_by_name(entry: str) -> None:
    """Scope File: an invalid entry is rejected with an error naming it."""
    with pytest.raises(scope.ScopeFileError, match=entry.replace(".", r"\.")):
        scope.parse_scope_text(f"## In Scope\n- {entry}\n")


def test_missing_scope_file_contributes_no_entries(tmp_path: Path) -> None:
    """Scope File: a missing scope file contributes no entries."""
    assert scope.read_scope_entries(tmp_path / "absent.md") == []


def test_unreadable_scope_file_is_an_error(tmp_path: Path) -> None:
    """Scope File: a scope file that is not UTF-8 text is an error."""
    path = tmp_path / "scope.md"
    path.write_bytes(b"## In Scope\n- \xff\xfe\n")
    with pytest.raises(scope.ScopeFileError):
        scope.read_scope_entries(path)


def test_scope_file_is_read_on_every_call(tmp_path: Path) -> None:
    """Scope File: the scope in effect is always the one on disk."""
    path = tmp_path / "scope.md"
    path.write_text("## In Scope\n- 10.0.0.1\n")
    assert scope.read_scope_entries(path) == [ipaddress.ip_network("10.0.0.1")]
    path.write_text("## In Scope\n- 10.0.0.2\n")
    assert scope.read_scope_entries(path) == [ipaddress.ip_network("10.0.0.2")]


def test_scope_file_path_comes_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scope File: the path is taken from RECON_SCOPE_FILE."""
    configured = tmp_path / "engagement.md"
    monkeypatch.setenv(scope.SCOPE_FILE_ENV, str(configured))
    assert scope.scope_file_path() == configured


def test_scope_file_path_defaults_to_working_directory(tmp_path: Path) -> None:
    """Scope File: without RECON_SCOPE_FILE, scope.md in the working directory is used."""
    assert scope.scope_file_path() == tmp_path / "scope.md"


def test_default_scope_file_is_loaded(tmp_path: Path) -> None:
    """Scope File: scope.md in the working directory is used if it exists."""
    (tmp_path / "scope.md").write_text("## In Scope\n- 10.0.0.1\n")
    assert scope.load_scope_entries() == [ipaddress.ip_network("10.0.0.1")]


def test_missing_configured_scope_file_is_detected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scope File: a configured but missing scope file is detected."""
    configured = tmp_path / "absent.md"
    monkeypatch.setenv(scope.SCOPE_FILE_ENV, str(configured))
    assert scope.missing_configured_scope_file() == configured


def test_existing_configured_scope_file_is_not_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scope File: an existing configured scope file is accepted."""
    configured = tmp_path / "engagement.md"
    configured.write_text(SPEC_EXAMPLE)
    monkeypatch.setenv(scope.SCOPE_FILE_ENV, str(configured))
    assert scope.missing_configured_scope_file() is None


def test_unset_environment_has_no_missing_scope_file() -> None:
    """Scope File: without RECON_SCOPE_FILE nothing is required to exist."""
    assert scope.missing_configured_scope_file() is None
