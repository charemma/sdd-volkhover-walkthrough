# Runtime Rule Conflict Log

This file records runtime rule conflicts and their resolutions. AI MUST append new entries below the separator, following the format shown in the template entry below.

## Entry format

Each entry uses the following structure. Fields appear in this order; do not omit any field, do not reorder. Verbatim content (user input, rule quotes) goes inside blockquotes (`>`).

**RC<NNN> — <YYYY-MM-DD ~HH:MM Z> — <user name>**

**User input:**
> [verbatim user input that triggered the conflict]

**Operation:** [one-line description of what AI was about to do]

**Conflicting rules:**

- From `<source-file>` § <section heading>:
  > [verbatim rule quote]
- From `<source-file>` § <section heading>:
  > [verbatim rule quote]

**Conflict explanation:**
[explanation of why the rules cannot both be satisfied for the current operation]

**Options presented:**

- [option a, e.g., drop one of the conflicting rules]
- [option b, e.g., custom resolution for this request]
- [option c, e.g., stop work]

**Decision:** [filled in when user responds, with timestamp]

---

(New entries appended below this separator, in order of occurrence.)
