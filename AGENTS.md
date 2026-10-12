## Project Intent

This project specifies `recon-mcp`, a small service for authorized penetration tests. It enumerates open TCP ports and identifies the services behind them, and it exposes both capabilities over an HTTP API and as MCP tools that an AI agent can call. Scans are restricted to an explicitly approved target scope. The specification is the source of truth; the implementation, container image, and deployment are built from it.

The project also serves as a worked example for a blog series on spec-driven development, following the method from Anatoly Volkhover's book _Agentic Spec-Driven Development_. It is not affiliated with the author.

## Rule Management

A durable rule is a rule that is part of the project's persistent rule set — recorded in AGENTS.md or in any `rules`-type file AGENTS.md references — and applied either on every turn (when always loaded) or when a specific trigger fires (when conditionally loaded). It is distinct from a one-off instruction that applies only to the current request, and distinct from any project-domain meaning of "rule" (business rule, validation rule, parsing rule, and the like).

- Durable rules MUST be recorded either in the `AGENTS.md` file at the project root or in a `rules`-type file that the project-root `AGENTS.md` references. Do not record durable rules in the user-global `AGENTS.md` or in any nested `AGENTS.md` inside a subfolder.

- For any work involving durable rules — creating a new durable rule, editing an existing one, removing one, or analyzing them — AI MUST read `rule-analysis.md` at the project root and MUST follow the protocol stated there.

- Changes to any file containing durable rules (additions, edits, deletions) MUST be recorded only after explicit user approval.

## Referenced Files

- When this `AGENTS.md` file references another file by name, AI MUST verify that the file exists before relying on its content. If a referenced file is missing, AI MUST report this to the user and ask whether to stop or to ignore the reference and continue.

## Input Relevance

- When a user input does not appear to align with the intent stated in the Project Intent section of this AGENTS.md file, AI MUST ask the user how the input relates to the project, and MUST continue asking until the relevance is established or the user issues a blind override — an explicit instruction to proceed without further inquiry.

## Rule Conflicts at Runtime

- A runtime rule conflict exists when two or more durable rules require incompatible behavior for the current operation and AI cannot satisfy both. Mere overlap — multiple rules applying to the same operation without incompatibility — does not constitute a conflict and MUST NOT trigger this protocol.

- On detecting a runtime rule conflict, AI MUST stop before producing or modifying any output that depends on the conflicting rules, append a log entry to `rule-conflict-log.md`, and follow the procedure in `rule-conflict-protocol.md`.

- AI MUST NOT guess a resolution, silently apply one rule over another, or proceed by inferring user intent — instead, present the conflict to the user with at least three options (drop one of the conflicting rules, propose a custom resolution, or stop) and resume work only as the user's decision permits.

- Writing an entry to `rule-conflict-log.md` is itself exempt from this rule.

## Undefined References

- When AI, while applying a rule, encounters a reference to another rule, a section, or a named entity that does not resolve to a definition in the `AGENTS.md` file or any `rules`-type file the `AGENTS.md` file references, AI MUST stop and ask the user to define the reference before proceeding. Do not infer the meaning of an undefined reference.

## Scratch Directory

The project root contains a single reserved directory named `.tmp/` for AI's transient working files.

- AI MUST place transient working files — one-off scripts, intermediate tool outputs, comparison drafts, anything not intended for the user to read as part of normal project work — in `.tmp/`.

- AI MAY create, modify, and delete files in `.tmp/` at any time without seeking approval from this rule.

- Files inside `.tmp/` MUST NOT be referenced from any registered file or any rule. Anything that needs to persist or be referred to MUST be promoted out of `.tmp/` and registered first.

- Exactly one scratch directory exists, at the project root. AI MUST NOT create additional scratch directories elsewhere in the project.

## File Registry

The File Registry is the project's index of every file in it, structured as a table where each row represents one registered file. Every change to the file inventory MUST be reflected here before the file system is touched. Subfolders are not registered separately — they are derived from the Subfolder column of registered files, and exist on disk by virtue of having at least one file placed in them.

### Structure

This section interprets the columns of the **Registered Files** table below — what each column holds and what values are valid.

#### Type

The Type column carries a categorical label describing what the file is. The set of permitted types is closed. Only the following type values are allowed:

- `rules` — a file containing durable rules in the project's rule format.
- `log` — a file accumulating timestamped entries.

AI MAY propose new types; AI MUST NOT introduce them silently. Adding a type requires explicit user approval and an entry here.

#### Protocol

The Protocol column carries a behavioral discipline applied to the file. The set of permitted protocols is closed. Only the following protocol values are allowed:

- `read-only` — AI MUST NOT modify or delete the file; the user MAY edit it directly. The `Dependencies` and `Instructions` columns MUST be left empty for this protocol.
- `append-only` — AI MAY only append new entries. AI MUST NOT delete or modify the file or any past entries; corrections MUST be added as new entries that reference the prior entry by its identifier. The user MAY still edit or delete the file directly. The `Dependencies` and `Instructions` columns MUST be left empty for this protocol.
- `editable` — no protocol-level restrictions on modification; AI MAY modify the file as needed. Deletion requires user approval per the **Inventory change** rule. The `Dependencies` and `Instructions` columns MUST be left empty for this protocol.

Every registered file MUST carry an explicit protocol value. AI MAY propose new protocols; AI MUST NOT introduce them silently. Adding a protocol requires explicit user approval and an entry here.

#### Extension

Registered file names use one extension separated by a single period. The extension is recorded in the Extension column. The set of permitted extensions is closed. Only the following extensions are allowed:

- `.txt`
- `.md`
- `.pdf`
- `.html`
- `.xlsx`
- `.docx`
- `.pptx`

AI MAY propose new extensions; AI MUST NOT introduce them silently. Adding an extension requires explicit user approval and an entry here.

#### Subfolder

The Subfolder column holds a path relative to the project root, expressed without leading or trailing slashes. A single-level subfolder appears as `name`; nested subfolders appear as `name1/name2`. The cell is empty when the file lives at the project root. Subfolder path segments MUST consist only of lowercase English letters (a–z), digits (0–9), dashes (`-`), and underscores (`_`); path segments MUST NOT contain a period.

Placement conventions:

- Files of type `log` SHOULD be placed in the `logs/` subdirectory unless a specific reason exists otherwise.

#### Description

Every registered file MUST have a non-empty Description.

The Description column carries a short free-text statement of what _kind_ of information the file holds and what role that kind of information plays in the project. A Description names the file's contents by category - the rule by which what goes into the file is determined - rather than summarizing what the file currently says. It determines routing when deciding where new information should go, and where to read the desired information from; it is an invitation to read the file when needed, not a replacement for reading it.

The rules that govern Description content - abstraction, non-overlap, and the enforcement check - are stated in the **Discipline** subsection below.

#### Dependencies

The Dependencies column lists other registered files that this file depends on. The value is a comma-separated list of registered file names, or empty when the file has no dependencies. Every entry MUST resolve to a registered file via the **Reference resolution** rule.

The use of this column — whether a file requires it, and what its entries signify — MUST be explicitly governed by the file's Protocol. Every Protocol MUST state how it uses or does not use this column.

#### Instructions

The Instructions column holds the registered name of a single file containing instructions associated with this file, or is empty. When non-empty, the value MUST resolve to a registered file via the **Reference resolution** rule, and the referenced file MUST have type `rules`.

The use of this column — whether a file requires it, and what the referenced file signifies — MUST be explicitly governed by the file's Protocol. Every Protocol MUST state how it uses or does not use this column.

### Discipline

- Inventory change. Any change to the project's file inventory — creation, deletion, rename, or move — MUST be reflected in the File Registry. AI MUST propose the registry update (a complete row for additions; the affected row for changes; the deletion target for removals) and obtain explicit user approval. Only after approval MAY AI write the registry update or perform the file-system operation.

- Naming convention. Registered file names and subfolder path segments MUST consist only of lowercase English letters (a–z), digits (0–9), dashes (`-`), and underscores (`_`). File extensions MUST follow the same restriction. AI MUST NOT register a non-conforming name and MUST propose a conforming alternative.

- Name uniqueness. No two entries in the File Registry MAY share the same combination of file name and extension, compared case-insensitively, regardless of subfolder. When a proposed file name collides with an existing entry, AI MUST flag the collision and propose a distinct name before registration.

- Path discipline. AI MUST place every registered file at the path recorded in its registry row (subfolder plus file name). Moving a file requires updating the row first; loose files outside their registered path MUST be flagged when detected.

- User-facing placement. AI MUST place files intended for the user to read or use as part of the project in their registered location, registering them first. Such files MUST NOT be placed in the scratch directory `.tmp/`.

- Registration tie-break. When uncertain whether a new file is transient or for human consumption, AI MUST treat it as for human consumption: propose a registry row and ask.

- Type-discipline lookup. Before reading or writing a registered file, AI MUST consult the file's Type and Protocol entries and apply the discipline they carry.

- Reference resolution. When a rule references a file by name, AI MUST resolve the reference against the File Registry's file rows. AI MUST NOT check disk presence for the purposes of reference resolution. Unresolved file references MUST trigger the **Undefined References** rule.

- Agent-imposed exemption. The file `AGENTS.md` is exempt from the Naming Convention, Name Uniqueness, Path Discipline, and Subfolder Convention rules — its name and location are dictated by the AI agent. The registry's Description field for `AGENTS.md` MUST note this agent-imposed nature.

- Scratch exemption. Files inside `.tmp/` are exempt from all File Registry rules — registration, naming, uniqueness, path discipline, type and protocol assignment. The scratch directory is governed by the **Scratch Directory** section above.

- Description abstraction. A Description MUST state what kind of information the file holds and what role that kind plays in the project. A Description MUST NOT summarize, paraphrase, or restate the file's current contents; it MUST describe the file by category, not by content snapshot. When a proposed Description summarizes content, AI MUST rewrite it to name the kind of information instead and present the rewrite to the user before the registry change proceeds.

- Description non-overlap. No two Descriptions in the File Registry MAY cover overlapping kinds of information. When a proposed Description's scope intersects an existing Description's scope, AI MUST flag the overlap, identify the overlapping rows, and offer resolution options - narrow the proposed Description, narrow the existing Description, narrow both descriptions, or consolidate the files under one Description - before the registry change proceeds.

- Description compliance check. Before AI proposes any addition or modification to the File Registry that introduces or changes a Description, AI MUST verify the proposed Description against the **Description abstraction** and **Description non-overlap** rules. If either check fails, AI MUST present the failure and the available resolution options, accept the user's choice, apply it without changing File Registry on disk, and re-run both checks. AI MUST repeat this loop until both checks pass; only then MAY AI present the proposed row to the user for approval under the **Inventory change** rule. This check has no override.

- Acyclicity. The Dependencies column entries of `generated` files MUST NOT form a chain that loops back on itself. A registry change that would introduce such a loop MUST be refused.

### Registered Files

| Subfolder                                    | File                        | Type  | Protocol    | Dependencies | Instructions | Description                                                                                                                                             |
| -------------------------------------------- | --------------------------- | ----- | ----------- | ------------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
|                                              | `AGENTS.md`                 | rules | editable    |              |              | Durable project rules and the index of all project files. \_Agent-imposed name and location (AGENTS.md convention, read by Claude Code and other coding |
| agents); see Agent-imposed exemption rule.\_ |
|                                              | `rule-analysis.md`          | rules | editable    |              |              | Rule analysis protocol — applies when creating or editing durable rules                                                                                 |
|                                              | `rule-conflict-protocol.md` | rules | editable    |              |              | Runtime rule conflict procedure — applies when a conflict is detected during request processing                                                         |
| `logs`                                       | `rule-conflict-log.md`      | log   | append-only |              |              | Audit log of runtime rule conflicts and their resolutions                                                                                               |
