# Runtime Rule Conflict Protocol

> Adapted from Anatoly Volkhover's book _Agentic Spec-Driven Development_ (https://agentic-spec.com).

This file defines the procedure AI MUST follow when a runtime rule conflict is detected. The procedure has three steps, executed in order:

- **Step 1: Log the Conflict**
- **Step 2: Present the Conflict**
- **Step 3: Act on the Decision**

## Step 1: Log the Conflict

AI MUST append a new entry to `rule-conflict-log.md` containing:

- A stable conflict ID in the format `RC###` (sequential numbering, never reused or renumbered).
- Local timestamp in the format `YYYY-MM-DD ~HH:MM Z — <user name>`.
- The user input that triggered the conflict, verbatim.
- A one-line description of the operation AI was about to perform.
- Verbatim quotes of each conflicting rule, with the source file and section heading each rule comes from.
- An explanation of why the rules cannot both be satisfied for the current operation.
- The options AI is presenting to the user.
- A `Decision:` line, left blank, to be filled when the user responds.

Format the entry per the template at the top of `rule-conflict-log.md`.

## Step 2: Present the Conflict

AI MUST present the user with:

- The list of conflicting rules, quoted verbatim, with their sources.
- The operation that surfaced the conflict.
- An explanation of why the rules cannot both be satisfied for this operation.
- At least three options — (a) drop one of the conflicting rules from `AGENTS.md`, (b) propose a custom resolution that applies only to the current request, (c) stop work on the request — and any other options AI considers reasonable.
- An explicit request for the user's instruction before AI proceeds.

## Step 3: Act on the Decision

When the user responds, AI MUST:

- Append the user's decision to the `Decision:` line of the original log entry, with timestamp.
- If the user chose to drop a rule, follow the standard rule-modification procedure in `rule-analysis.md` (analysis steps + explicit approval) before removing the rule.
- If the user proposed a custom resolution, apply it only to the current request — do not generalize it into a new rule unless the user explicitly instructs.
- If the user chose to stop, halt work on the request and produce no further output beyond confirmation.
