# recon-mcp

recon-mcp is a small service for authorized penetration tests. It finds open TCP ports on a target, identifies the services behind them, and exposes both over an HTTP API and as MCP tools an AI agent can call. It only scans targets inside an explicitly approved scope. So far it implements TCP port enumeration over HTTP.

The project is also a worked example for a blog series on spec-driven development. The specs in `.ai/specs/` are the source of truth, and the implementation is built from them. The rules that drive this process live in `AGENTS.md` and `.ai/`.

## Attribution

The bootstrap material (`rule-analysis.md`, `rule-conflict-protocol.md` and parts of `AGENTS.md`) comes from Anatoly Volkhover's book _Agentic Spec-Driven Development_ (https://agentic-spec.com). This project is not affiliated with the author.
