---
name: manage-version
type: capability
version: 0.1.0
description: Owns SemVer, changelog, deprecation, impact analysis, release readiness, and the release transition.
triggers:
  - GENERATE stage entered (initial versions and changelog)
  - IMPACT_ANALYSIS or VERSION stage entered
  - RELEASE_READINESS or RELEASE stage entered
inputs:
  - artifacts
  - prior_versions
  - change_summary
  - dependency_graph
  - package_state
outputs:
  - version_plan
  - changelog_entry
  - deprecation_updates
  - release_report
dependencies:
  - knowledge/schemas.md
---

# Purpose

Maintain coherent artifact versioning and lifecycle state, and decide whether a package may be released.

# Scope

In scope: initial versions, SemVer classification, `CHANGELOG.md`, deprecation, dependency impact, release readiness, the release transition.

Out of scope: substantive content authoring, running validation or tests.

# Inputs

- `artifacts`
- `prior_versions`
- `change_summary`
- `dependency_graph`
- `package_state`: gate results, open issues, waivers, and policy.

# Outputs

```yaml
version_plan:
  artifacts:
    - path: string
      old_version: string | null
      new_version: string
      change_class: major | minor | patch | initial
      rationale: string
  package_version: string
changelog_entry: string
deprecation_updates: []
release_report:
  release_ready: boolean
  failed_conditions: [string]
```

# Dependencies

- `knowledge/schemas.md`

# Rules

- Versions are final before VALIDATE. In CREATE, new artifacts get `0.1.0`; in REFACTOR and VERSION, VERSION runs before VALIDATE.
- While MAJOR is 0, a breaking change bumps MINOR and a compatible change bumps PATCH. Promotion to `1.0.0` is a deliberate change, made with its own changelog entry before validation.
- Breaking public contract or removal: MAJOR. Backward-compatible feature or capability addition: MINOR. Backward-compatible correction or clarification: PATCH. Deprecation: MINOR.
- Package version and policy overrides follow Policy Defaults in `knowledge/schemas.md`. Components version independently; unchanged artifacts keep their version.
- Every version change requires a `CHANGELOG.md` entry. Format: `## <package_version> — YYYY-MM-DD`, then one line per changed artifact: `- <path> <old> → <new> (<change_class>): <summary>`; new artifacts: `- <path> <version> (initial): <summary>`.
- Never modify a released artifact in place.
- IMPACT_ANALYSIS: map dependents of every changed public contract before assigning versions.
- RELEASE_READINESS: evaluate `release_ready` from Policy Defaults against the current content_hash. Missing or STALE gate results fail the predicate. Draft artifacts become `validated` only when it holds.
- RELEASE: requires a recorded CONFIRM_RELEASE. Re-evaluate the predicate; any change since readiness blocks release. Set `lifecycle: released` and record each content_hash in package state. Edit no artifact files.
- Deprecation: set `status: deprecated` and the `deprecation` block (see `knowledge/schemas.md`) in a new version. Do not create new dependencies on deprecated artifacts unless the user approves.

# Failure Modes

- `INPUT_ERROR`: version/change data missing.
- `LOGIC_ERROR`: change class ambiguous.
- `DEPENDENCY_ERROR`: affected dependents unresolved.
- `VALIDATION_ERROR`: metadata inconsistent or release predicate not met.
- `AUTHORIZATION_ERROR`: release attempted without CONFIRM_RELEASE.
- `USER_ACTION_REQUIRED`: version interpretation unresolved.

# Error Handling & Safety

Never bump a version without a changelog entry. Never release without recorded confirmation. Escalate ambiguous public-contract changes.
