---
name: review-refactor
type: capability
version: 0.1.0
description: Reviews existing packages, proposes changes, and applies confirmed refactors and autofixes without silently changing intent.
triggers:
  - REVIEW, PROPOSE_CHANGES, or REFACTOR stage entered
  - validation reports autofix-class revisions
inputs:
  - existing_artifacts
  - requested_changes
  - user_criteria
  - required_revisions
outputs:
  - review_report
  - change_plan
  - refactored_artifacts
  - impact_report
dependencies:
  - knowledge/schemas.md
  - knowledge/best-practices.md
optional_dependencies:
  - knowledge/safety-policies.md
---

# Purpose

Improve existing artifacts while preserving intended behavior unless an intentional change is explicitly approved.

# Scope

In scope: review, duplicate detection, artifact-boundary analysis, reference/dependency impact, change proposal, confirmed refactor, applying autofixes, identifying scenarios to rerun.

Out of scope: silent redesign, running validation, version assignment (see `capabilities/manage-version.md`).

# Inputs

- `existing_artifacts`
- `requested_changes`
- `user_criteria`
- `required_revisions`: validator revisions carrying an `autofix_class`.

# Outputs

```yaml
review_report:
  findings:
    critical: []
    major: []
    minor: []
  evidence: []
change_plan:
  files_to_change: []
  files_to_add: []
  files_to_remove: []
  intent_changes: []
  version_impacts: []
  tests_to_rerun: []      # scenario ids from tests/scenarios.yaml
impact_report:
  dependents: []
  affected_gates: []
refactored_artifacts: []   # files changed by a confirmed REFACTOR or by autofixes
```

The change set to confirm is the union of `files_to_change`, `files_to_add`, and `files_to_remove`.

# Dependencies

- `knowledge/schemas.md`
- `knowledge/best-practices.md`
- `knowledge/safety-policies.md` (optional)

# Rules

- REVIEW never writes.
- REFACTOR requires confirmation of the change plan first.
- Preserve intent unless behavior change is explicitly approved.
- Map downstream references before changing names, paths, contracts, or versions.
- Never modify released artifacts in place.
- Extract facts only when artifact-selection rules justify it; split only when decomposition criteria are met.
- Update README and file inventory when package contents change.
- Autofix: apply only the autofix classes listed in `knowledge/schemas.md` (Policy Defaults), inside the confirmed file list, once per validation failure; report every autofix to the user.
- Package not produced by this system (no state, versions, or conforming frontmatter): review it as a baseline, report non-conformance as findings, and propose a conformance change set rather than rewriting.
- Review against `target_llm` when the brief or request names one.

# Failure Modes

- `INPUT_ERROR`: incomplete/unreadable package.
- `LOGIC_ERROR`: intent cannot be determined.
- `REFERENCE_ERROR`: downstream references cannot be mapped.
- `DEPENDENCY_ERROR`: refactor would invalidate dependency graph.
- `SECURITY_ERROR`: controls weakened or sensitive data exposed.
- `USER_ACTION_REQUIRED`: behavior change or deletion needs approval.

# Error Handling & Safety

Require explicit approval for behavior changes and deletion. Redact secrets/PII before refactoring sensitive content. Anything outside the autofix classes escalates.
