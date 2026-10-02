---
name: design-readme
type: capability
version: 0.1.0
description: Produces the single human-facing README from actual package contents and metadata.
triggers:
  - artifact_plan.readme is true
inputs:
  - design_brief
  - artifact_plan
  - generated_artifacts
outputs:
  - README.md content
dependencies:
  - knowledge/schemas.md
---

# Purpose

Generate concise human-facing package documentation derived from the actual package.

# Scope

In scope: the canonical README outline below, file inventory, capability table.

Out of scope: authoritative runtime rules, private architect state, the changelog (owned by `capabilities/manage-version.md`).

# Inputs

- `design_brief`
- `artifact_plan`
- `generated_artifacts`: actual generated files and their frontmatter metadata.

# Outputs

One root `README.md` with these level-2 headings in order: `Purpose`, `Quick Start`, `Inputs and Outputs`, `Architecture`, `Capabilities`, `Limitations`, `Files`. Extra sections may follow `Architecture`.

# Dependencies

- `knowledge/schemas.md`

# Rules

- Audience: users and reviewers. Run last in GENERATE, after versions are final.
- Artifact metadata is authoritative for names, versions, and paths.
- Capability table columns are exactly `Capability`, `Description`, `Version`; write `None.` when there are no capabilities.
- `Files` lists every package file (a directory entry covers the files beneath it) and nothing that does not exist. Include `CHANGELOG.md` and `tests/scenarios.yaml`.
- Do not expose secrets, credentials, raw PII, private endpoints, or architect-only state.
- Do not maintain operational rules that can be derived from artifacts.
- Keep prose concise.

# Failure Modes

- `LOGIC_ERROR`: README claims unsupported behavior.
- `DEPENDENCY_ERROR`: metadata unavailable.
- `VALIDATION_ERROR`: table or file inventory drift.

# Error Handling & Safety

Do not document unsafe behavior as supported. Escalate when public documentation cannot be reconciled with the package.
