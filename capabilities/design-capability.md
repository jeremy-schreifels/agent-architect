---
name: design-capability
type: capability
version: 0.1.0
description: Authors one reusable, independently bounded capability artifact.
triggers:
  - artifact_plan.capabilities is non-empty
inputs:
  - design_brief
  - capability_spec
outputs:
  - capability.md content
dependencies:
  - knowledge/schemas.md
  - knowledge/best-practices.md
optional_dependencies:
  - knowledge/safety-policies.md
---

# Purpose

Author one reusable capability with an explicit contract, boundary, failure model, and handoff behavior.

# Scope

In scope: one reusable operation, I/O, dependencies, failures, tools, permissions, escalation, handoff.

Out of scope: parent orchestration, runtime domain knowledge, README.

# Inputs

- `design_brief`
- `capability_spec`: one entry of `artifact_plan.capabilities` (`name`, `job`, `inputs`, `outputs`, `tools`).

# Outputs

One `capabilities/<name>.md` conforming to Capability Schema in `knowledge/schemas.md`. New artifacts start at `version: 0.1.0`.

# Dependencies

- `knowledge/schemas.md`
- `knowledge/best-practices.md`
- `knowledge/safety-policies.md` (optional)

# Rules

- One capability = one job; state scope and non-goals.
- Write the `Dependencies` heading from the frontmatter lists so the two never differ.
- Use structured I/O where composition benefits from it.
- When `tools` is declared, add a `Tools` heading with Tool Contracts.
- Map failures to the shared error taxonomy and define recovery or escalation.
- Define handoff expectations.
- Reference reusable/volatile domain facts rather than embedding them.

# Failure Modes

- `LOGIC_ERROR`: multiple unrelated jobs.
- `DEPENDENCY_ERROR`: unavailable/circular dependency.
- `SECURITY_ERROR`: unsafe action without controls.
- `CONFIGURATION_ERROR`: incomplete tool/permission configuration.
- `USER_ACTION_REQUIRED`: authorization/design decision missing.

# Error Handling & Safety

Irreversible or high-impact actions require HITL. Never bypass policy or authorization.
