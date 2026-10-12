# enum_ports

## Purpose

During an authorized penetration test, the tester needs to know which TCP ports on a target host accept connections. enum_ports answers that question for a single host and a caller-supplied set of ports. It is the first step of reconnaissance; service identification builds on its results.

## Scope Restriction

Scanning hosts without authorization is harmful and may be illegal. enum_ports therefore only scans targets that are explicitly approved.

- A target MUST be scanned only if it is in scope.
- A target is in scope if it is a loopback target or matches an entry of the scope file.
- A request for a target that is not in scope MUST be rejected with an error, and no network traffic MUST be sent to that target.

### Loopback Targets

Scanning the local machine never reaches a third party, so all common ways of addressing it are always in scope, without any configuration:

- any IPv4 address in `127.0.0.0/8`
- the IPv6 loopback address `::1`
- IPv4-mapped loopback addresses (`::ffff:127.0.0.0/104`)
- the hostname `localhost`

`0.0.0.0` and `::` are not loopback targets and are treated like any other address.

## Scope Sources

Operators define the approved scope per engagement in a scope file, kept as a reviewable document next to the engagement records. The scope file is the only scope source; the effective scope is its entries plus the loopback targets.

### Entries

- An entry is a single IP address (IPv4 or IPv6) or a CIDR range (for example `10.0.0.0/24`).
- A target matches an entry if it is the same address or lies inside the range.
- Hostnames are not valid entries, because their resolution can change after the scope was approved.
- An IPv4-mapped IPv6 target (for example `::ffff:10.20.1.15`) does not match an IPv4 entry, and an IPv4 target does not match an IPv4-mapped IPv6 entry. Only loopback targets get this mapping treatment.

### Scope File

A scope file is a Markdown document that records the approved scope of an engagement in a form people can read, review, and version.

- The scope file path is taken from the environment variable `RECON_SCOPE_FILE`. If the variable is unset, the file `scope.md` in the service's working directory is used if it exists.
- If `RECON_SCOPE_FILE` is set and the file does not exist, the service MUST refuse to start.
- The entries are the list items under the heading `## In Scope`, one entry per list item. Everything else in the file is free text and is ignored, so the file can also hold engagement details such as client, contact, and time window.
- The `## In Scope` section ends at the next heading of level 1 or 2.
- A list item is a line starting with `-`, `*`, or `+` followed by a space; surrounding whitespace of the entry is ignored.
- If the scope file exists but cannot be read as UTF-8 text, the scan request MUST be rejected with an `invalid_scope_file` error.
- If any entry under `## In Scope` is invalid, the scan request MUST be rejected with an error naming the invalid entry.
- The scope file is read on every scan request, so the scope in effect is always the one on disk.
- If no scope file exists when a request is processed, it contributes no entries; only loopback targets are in scope.

Example:

```markdown
# Scope: ACME internal test, 2026-10

Authorized by: J. Doe, ACME CISO. Window: 2026-10-12 to 2026-10-16.

## In Scope

- 10.20.0.0/24
- 10.20.1.15
```

## Port Probing

- A port is open if a TCP connection to it completes within 1 second; otherwise it counts as closed or filtered.
- At most 100 ports are probed concurrently per request.
- The target `localhost` is probed at `127.0.0.1`, without name resolution.

## Service Startup

- The service listens for HTTP requests on `127.0.0.1:8000`. The address is fixed; making it configurable is planned for a later iteration.

## Interface

### Request

`POST /scan` with a JSON body:

| Field                      | Type              | Meaning                                                                                  |
| -------------------------- | ----------------- | ---------------------------------------------------------------------------------------- |
| `target`                   | string            | The single host to scan: an IP address or `localhost`.                                   |
| `ports`                    | array of int      | The TCP ports to check on the target.                                                    |

### Successful Response

Status `200`, JSON body:

```json
{
  "target": "10.20.1.15",
  "open_ports": [22, 80]
}
```

- `open_ports` contains the ports from the request that were found open on the target, in ascending order and without duplicates. Ports that are closed or filtered are not included. An empty list means no requested port was open.

### Error Response

Every error uses the same JSON body, so callers can handle failures uniformly:

```json
{
  "error": {
    "code": "target_not_allowed",
    "message": "Target 10.0.0.5 is not in scope."
  }
}
```

`code` is a stable machine-readable identifier; `message` is human-readable and may change.

| Situation                                                          | Status | `code`               |
| ------------------------------------------------------------------ | ------ | -------------------- |
| Body is not valid JSON or a field is missing or has the wrong type | `400`  | `invalid_request`    |
| `target` is neither a valid IP address nor `localhost`             | `400`  | `invalid_target`     |
| `ports` is empty or contains a value outside 1-65535               | `400`  | `invalid_ports`      |
| Target is not in scope                                             | `403`  | `target_not_allowed` |
| The scope file contains an invalid entry or cannot be read         | `500`  | `invalid_scope_file` |

## Input Validation

Invalid requests are rejected before any scan happens.

- `target` MUST be a literal IPv4 or IPv6 address, or the hostname `localhost`. Other hostnames are rejected, because resolving them could lead to scanning an address the caller did not name.
- `ports` MUST contain at least one port.
- Every port MUST be an integer from 1 to 65535.
- A port value that is not a JSON integer (for example `true` or `22.5`) is a wrong type and reported as `invalid_request`; an integer outside 1-65535 is reported as `invalid_ports`.
- Unknown fields in the request body are ignored.
- Duplicate ports are allowed and are checked once.
- Input validation happens before the scope check; an invalid target is reported as `invalid_target`, not `target_not_allowed`.
- When a request has several problems, only the first one in this order is reported: `invalid_request`, `invalid_target`, `invalid_ports`, `invalid_scope_file`, `target_not_allowed`.

## Out of Scope

- Scanning multiple hosts or networks in one request.
- UDP ports.
- Identifying the services behind open ports.
- Exclusion lists within the scope (for example an "Out of Scope" section in the scope file).
- Runtime verification of the scope file (e.g. git state); auditability comes from versioning the file and, later, the audit log.
- Exposing enum_ports as an MCP tool; planned for a later iteration.
