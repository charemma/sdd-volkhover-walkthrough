# Glossary

Terms used in this project's rules, specs and conversation. Each entry states what the term means here and what it does not mean. Where another file defines a term normatively, the entry names that file and the definition there wins.

## souvlaki-case

- Meaning: synonym for kebab-case; lowercase words joined by dashes, e.g. `enum-ports`.
- Not: snake_case or camelCase; also not the File Registry naming convention, which additionally allows underscores and digits.

## target

- Meaning: the single host a scan request names.
- Not: a network or range, an arbitrary hostname, or an entry of the scope file.
- Defined in: `001-enum-ports.md`

## in scope

- Meaning: approved for scanning, either as a loopback target or by matching an entry of the scope file.
- Not: the feature boundary described in a spec's "Out of Scope" section, nor authorization in any wider sense the scope file does not express.
- Defined in: `001-enum-ports.md`

## loopback target

- Meaning: a target that addresses the local machine through its loopback interface and is therefore always in scope.
- Not: wildcard or unspecified addresses, the machine's own non-loopback addresses, or hostnames other than the one the spec names.
- Defined in: `001-enum-ports.md`

## scope file

- Meaning: the operator-maintained Markdown document that records the approved scope of one engagement.
- Not: a registered project file, repository configuration, or a machine-format allowlist such as YAML or JSON.
- Defined in: `001-enum-ports.md`

## open port

- Meaning: a requested TCP port on the target that accepts a connection.
- Not: a closed or filtered port, a UDP port, or a port whose service has been identified.
- Defined in: `001-enum-ports.md`
