---
name: validate-artifacts
type: capability
version: 0.1.0
description: Runs deterministic and semantic quality gates against contracts, integrity, safety, best practices, and acceptance criteria.
triggers:
  - VALIDATE stage entered
  - RELEASE_READINESS needs current gate results
inputs:
  - artifacts
  - package_state
  - design_brief
  - user_criteria
outputs:
  - validation_report
  - package_state_update
dependencies:
  - knowledge/schemas.md
  - knowledge/best-practices.md
optional_dependencies:
  - knowledge/safety-policies.md
  - knowledge/authority-hierarchy.md
---

# Purpose

Determine whether a package is structurally valid, internally consistent, safe, aligned with criteria, and ready for its requested lifecycle transition.

# Scope

In scope: static validation, integrity, contracts, safety, best practices, criteria, references, dependencies, README synchronization, knowledge metadata, scenario structure, staleness.

Out of scope: writing files (this capability only reports), executing scenarios (see `capabilities/test-artifacts.md`), claiming runtime correctness.

# Inputs

- `artifacts`
- `package_state`
- `design_brief`
- `user_criteria`: `design_brief.acceptance_criteria`, or user-supplied for existing packages.

Missing `user_criteria` makes the CRITERIA gate `BLOCKED`; never invent criteria.

# Outputs

```yaml
validation_report:
  artifact_state:
    package_version: string
    content_hash: string
    artifacts: [{path: string, version: string, content_hash: string}]
  gates:
    - name: string
      scope: package | <artifact-path>
      status: PASS | FAIL | BLOCKED | NOT_APPLICABLE | STALE
      findings:
        critical: [string]
        major: [string]
        minor: [string]
      waived: [string]
      evidence: [string]
  overall: PASS | FAIL | BLOCKED | NOT_APPLICABLE | STALE
  required_revisions:
    - {id: string, gate: string, severity: critical | major | minor, autofix_class: string | null, description: string}
package_state_update:     # proposed update for the caller to record
  gates: [{name: string, scope: string, status: string, version: string, content_hash: string}]
  open_issues: [{id: string, severity: string, description: string, status: open}]
```

# Dependencies

- `knowledge/schemas.md`
- `knowledge/best-practices.md`
- `knowledge/safety-policies.md` (optional)
- `knowledge/authority-hierarchy.md` (optional)

# Rules

Gate applicability, overall aggregation, and severity follow `knowledge/schemas.md` (Gate Applicability, Severity). Gates:

1. `PARSE`: YAML/Markdown parse.
2. `SCHEMA`: fields, headings, SemVer, lifecycle (released artifacts unchanged).
3. `REFERENCES`: internal references resolve; `CHANGELOG.md` covers current versions.
4. `CONTRACT`: triggers, I/O, tools, permissions, failure modes coherent; error tokens in the taxonomy.
5. `BEST_PRACTICES`: answer each applicable item in the best-practices checklists (BP-*, CT-*) yes/no with evidence.
6. `SAFETY`: answer each item in the safety checklist (SF-*) from `knowledge/safety-policies.md`.
7. `KNOWLEDGE`: provenance, authority, scope, freshness, conflicts valid for the knowledge class.
8. `DEPENDENCIES`: graph resolves; no cycles; deprecated-dependency policy applied.
9. `README`: canonical headings, capability table, and file inventory match the package.
10. `CRITERIA`: every acceptance criterion has evidence.
11. `REGRESSION`: scenario results from `capabilities/test-artifacts.md` (this capability checks structure only).

Procedure:

- Run `scripts/validate.py` through `code_exec` for gates 1-4 and 7-9 and for hashes, then add judgment only for BEST_PRACTICES, SAFETY, and CRITERIA. If the script cannot run, those gates are `BLOCKED` (`ENVIRONMENT_ERROR`).
- Tie every result to the exact `(version, content_hash)`. Any change makes affected results `STALE`.
- Never mark PASS without evidence.
- Waivers: exclude waived findings from status and list them under `waived`; a waiver tied to an older content_hash is STALE and ignored.
- Do not write files. For revisions fixable by an autofix class (`knowledge/schemas.md`, Policy Defaults) set `autofix_class`; otherwise `null`. Applying fixes belongs to `capabilities/review-refactor.md`.
- Check that nothing in the artifacts contradicts `target_llm` when it is set.

# Failure Modes

- `INPUT_ERROR`: required input missing.
- `REFERENCE_ERROR`: broken reference.
- `DEPENDENCY_ERROR`: missing/circular/incompatible dependency.
- `VALIDATION_ERROR`: gate condition fails, including schema and contract violations.
- `SECURITY_ERROR`: required safety control missing.
- `ENVIRONMENT_ERROR`: validation tooling unavailable.
- `USER_ACTION_REQUIRED`: unresolved criteria/design decision.

# Error Handling & Safety

Never reuse PASS from an older artifact state. Safety failures block release.
