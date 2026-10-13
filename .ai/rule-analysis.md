# Rule Analysis Protocol

> Adapted from Anatoly Volkhover's book _Agentic Spec-Driven Development_ (https://agentic-spec.com).

This file states the protocol AI MUST follow when creating a new durable rule, editing an existing one, or analyzing them.

## Formatting Conventions

All durable rules MUST follow these conventions:

(a) Group rules by topic under H2 (`##`) headings.

(b) State one requirement per rule. Do not combine multiple requirements into a single paragraph.

(c) Use imperative voice with priority markers — MUST for required behavior, SHOULD for recommended behavior, MAY for optional behavior. Default to passive or bare imperative form (no "you", no "AI" subject) unless actor disambiguation is required.

(d) Pair every prohibition with the recommended alternative.

(e) When a rule depends on a long protocol or list, place the detail in a separate file and reference it instead of embedding it.

(f) When a rule references a file, cite the file by its registered name (e.g., `rule-analysis.md`). Do not refer to a file by type, description, or alias.

## Analysis Steps

This protocol covers three operations on durable rules: adding a new rule, editing an existing rule, and removing a rule. The required steps differ by operation; all three require explicit user approval before the change is committed.

When **adding or editing a rule**, AI MUST perform Steps 1–4 below and present the results to the user. Record the change only after explicit user approval.

When **removing a rule**, AI MUST perform Steps 5–6 below and present the results to the user. Remove the rule only after explicit user approval. If Step 6 finds that other rules reference the one being removed, AI MUST refuse to remove it until those referencing rules are removed first (each removal subject to this same protocol).

### 1. List the Rule's Intents

State, in a structured list, what the rule requires, allows, and forbids. Include both explicit claims and implicit ones the wording does not foreground. The goal is to surface what the user is actually approving.

### 2. Flag Behavioral Conflicts

Read the proposed rule against every durable rule already recorded in `AGENTS.md` and in any `rules`-type file `AGENTS.md` references. Flag direct contradictions, deadlock risks, races for the same resource, and rules whose requirements would compose in unintended ways. When in doubt, ask the user for clarification rather than assume the conflict is benign.

### 3. Verify Formatting

Confirm that the proposed rule conforms to the formatting conventions stated above. If it does not, rewrite it into the conforming form and present the rewritten version alongside the original.

### 4. Verify References

For every file reference in the proposed rule, classify whether the rule treats the file as pre-existing by the time the rule executes. For pre-existing references, confirm that the file is registered in the **File Registry**; flag any reference whose target is not registered, and ask the user to either register the file or rewrite the rule to remove the reference.

Present the results as a list, one entry per file reference, showing: the cited file name, the classification (pre-existing, created by the rule, or guarded by an existence check), and the registered location (subfolder/file name, e.g., `x.md` or `y/x.md`) if the file is registered.

### 5. List the Removed Rule's Intents

State, in a structured list, what the rule was requiring, allowing, and forbidding. The goal is to surface what behavior is being removed from the project's rule set.

### 6. Find Referencing Rules

For every durable rule recorded in `AGENTS.md` or in any `rules`-type file `AGENTS.md` references, check whether it references the rule being removed. Present the list of referencing rules. If the list is non-empty, the removal is blocked until those rules are themselves removed.
