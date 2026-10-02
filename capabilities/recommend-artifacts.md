---
name: recommend-artifacts
type: capability
version: 0.1.0
description: Selects the minimum sufficient artifact set and the change-set file list from a design brief.
triggers:
  - DESIGN stage entered
inputs:
  - design_brief
outputs:
  - artifact_plan
dependencies:
  - knowledge/schemas.md
  - knowledge/best-practices.md
---

# Purpose

Choose the smallest architecture that preserves reuse, testability, provenance, maintainability, and efficiency, and present it as a confirmable change set.

# Scope

In scope: decomposition, capability/knowledge selection, README and test selection, file list.

Out of scope: authoring, execution, file writes.

# Inputs

`design_brief` conforming to Design Brief in `knowledge/schemas.md`. Required brief fields must be present.

# Outputs

`artifact_plan` conforming to Artifact Plan in `knowledge/schemas.md`: capability and knowledge entries are objects (`capability_spec`, `knowledge_spec`), and `file_list` is the change set to confirm.

# Dependencies

- `knowledge/schemas.md`
- `knowledge/best-practices.md`

# Rules

- Keep content inline when it is small, stable, local, intrinsic to the procedure, and not independently reusable.
- Create a capability when it is independently reusable/testable, materially complex, independently versioned, or has a distinct failure/recovery contract. Do not split tiny local operations for hypothetical reuse.
- Create knowledge when information is reusable, volatile, provenance-sensitive, access-controlled, or large enough for selective retrieval.
- Express user/system-specific choices as declared parameters in the skill `Inputs`. Do not create a configuration artifact.
- Keep runtime/architect state out of knowledge.
- Default files: `skill.md`, `tests/scenarios.yaml`, one root `README.md`, `CHANGELOG.md`. Set `readme` or `tests` to false only with a recorded rationale.
- `file_list` lists every file to add, change, or remove. Nothing outside it is written.

# Failure Modes

- `INPUT_ERROR`: incomplete brief.
- `LOGIC_ERROR`: overlapping/circular boundaries.
- `DEPENDENCY_ERROR`: unresolvable dependency.
- `USER_ACTION_REQUIRED`: materially different decompositions cannot be resolved.

# Error Handling & Safety

Do not silently merge overlapping capabilities or create dependency cycles. Flag safety-sensitive plans for applicable controls.
