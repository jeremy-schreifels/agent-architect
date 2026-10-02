---
name: schemas
type: knowledge
version: 0.1.0
description: Canonical schemas and policies for artifacts, tools, scenarios, briefs, plans, package state, gates, release readiness, and errors.
triggers:
  - artifact authoring
  - schema validation
  - package validation
  - lifecycle state management
inputs:
  - artifact or package state
outputs:
  - canonical contract and validation rules
dependencies: []
knowledge_class: static
---

# Facts

## Glossary

- artifact: any package file under lifecycle control (skill, agent, capability, knowledge, README, CHANGELOG, scenarios).
- skill: the generated root behavior artifact `skill.md`. agent: the root artifact of this system, `agent.md`.
- capability: a reusable operation in `capabilities/*.md`.
- package: the directory of artifacts for one skill (or for this architect). Package state is stored outside it.
- change set: the explicit list of files to add, change, or remove that the user confirms.

## Common Frontmatter

All artifacts with frontmatter MUST include:

```yaml
name: <kebab-case>
type: skill | agent | capability | knowledge
version: <semver>
description: <string>
triggers: [<string>]
inputs: [<string>]
outputs: [<string>]
```

Optional, all types: `tools`, `dependencies`, `optional_dependencies`, `status`, `deprecation`, `non_triggers`.
Optional, type-specific: `safety` (agent only), `knowledge_class` (knowledge only).
No undeclared frontmatter fields are permitted.

- `tools`: tool names. Each name MUST have a Tool Contract under the `Tools` heading.
- `dependencies`, `optional_dependencies`: package-root-relative artifact paths. Direct dependencies only; transitive loading is implicit.
- `non_triggers`: situations where the artifact MUST NOT be used.
- `status`: `active | deprecated` (default `active`). Lifecycle (draft, validated, released) lives in Package State, never in frontmatter.
- `deprecation`: required iff `status: deprecated`: `{effective: YYYY-MM-DD, replacement: <path-or-null>, reason: <string>, removal_target: <YYYY-MM-DD-or-null>}`.
- `safety` (agent): `{refusal: boolean, escalation: boolean, human_in_the_loop: <string>}`.
- `knowledge_class`: `static | managed` (default `managed`).
- Items in `inputs`/`outputs` written as snake_case identifiers MUST appear in the artifact's `Inputs`/`Outputs` section.

## Artifact Schemas

Required headings (level-1) by type:

- skill: `Overview`, `Inputs`, `Outputs`, `Capabilities`, `Instructions`, `Tools`, `Examples`, `Edge Cases`, `Error Handling & Safety`.
- agent: all skill headings plus `Operating Modes`, `Workflow Logic`.
- capability: `Purpose`, `Scope`, `Inputs`, `Outputs`, `Dependencies`, `Failure Modes`, `Error Handling & Safety`; plus `Tools` when `tools` is declared.
- knowledge, `static`: `Facts`, `Policies`, `Guidance`, `Provenance`.
- knowledge, `managed`: static headings plus `Freshness`, `Conflicts`, `Retrieval Hints`.

Rules:

- Capability `Dependencies` heading lists exactly the paths in `dependencies` and `optional_dependencies`.
- Skill/agent `Capabilities` heading lists capability paths used, or `None.`; each MUST be a declared dependency.
- `Examples` holds at least one minimal example; add counterexamples only where they clarify likely ambiguity.
- `Guidance` is domain guidance, not executable orchestration.
- Knowledge entries (see Knowledge Entry) are REQUIRED for `managed` knowledge and MAY be prose bullets for `static` knowledge.
- Parameters (user/system-specific choices) are declared inline in skill `Inputs`. There is no configuration artifact.
- Generated package layout: `skill.md`, `capabilities/`, `knowledge/`, `tests/scenarios.yaml`, `README.md`, `CHANGELOG.md`. README, CHANGELOG, and scenarios have no frontmatter and no own version.

## Structured I/O Contract

When labels are insufficient for composition:

```yaml
- name: <string>
  type: string | number | boolean | object | array | enum | reference
  required: true | false
  schema_ref: <relative-path-or-null>
  allowed_values: [<string>] | null
  nullable: true | false
```

## Tool Contract

```yaml
- name: <tool-name>
  purpose: <string>
  inputs: <schema-or-reference>
  outputs: <schema-or-reference>
  permissions: [<string>]
  side_effects: none | reversible | irreversible | high_impact
  authorization: user | system | delegated | none
  failure_modes: [<error-class>]
  modes: [<operating-mode>]      # optional; omitted = all modes
  constraints: <string>          # optional usage rules
```

Runtime-supplied function schemas, when present, govern parameter syntax only. The contract governs permissions, side effects, authorization, and failure behavior.

## Scenario Format

Stored in `tests/scenarios.yaml` as a list:

```yaml
- id: <kebab-id>
  target: <artifact path>
  type: static | runtime
  input: <string | object>
  expected_behavior: <observable, checkable behavior>
  pass_criteria: <string>
```

- `static`: dry-run of the artifact text against the scenario. `runtime`: executed on a live runtime.
- Result: `{id, status: PASS | FAIL | BLOCKED, mode: static | runtime, evidence}`. A runtime scenario with no execution infrastructure is `BLOCKED`.
- Minimum set for a generated skill: at least one scenario per declared trigger and per safety/error behavior.
- Static results never support runtime-correctness claims.

## Knowledge Entry

```yaml
id: <stable-id>
statement: <atomic proposition>
source: <source identifier>
authority_type: regulatory | contractual | organizational | internal | factual | technical | expert | secondary
authority_tier: 1-8
scope: <applicability>
effective_from: <date-or-null>
reviewed_at: <date>
expires_at: <date-or-null>
status: verified | provisional | unverified | deprecated
```

## Design Brief

```yaml
purpose: string                  # required
triggers: [string]               # required
non_triggers: [string]
inputs: [string]                 # required
outputs: [string]                # required
acceptance_criteria: [string]    # required; observable pass conditions; never invented by the architect
constraints: [string]
tools: [string]
edge_cases: [string]
safety_requirements: [string]
authorization_requirements: [string]
target_llm: string               # default "unspecified"
open_questions: [string]
assumptions: [string]
```

`user_criteria` (used by validation) is `acceptance_criteria`.

## Artifact Plan

```yaml
artifact_plan:
  skill: true
  capabilities:                  # each entry is a capability_spec
    - {name: string, job: string, inputs: [string], outputs: [string], tools: [string]}
  knowledge:                     # each entry is a knowledge_spec
    - {name: string, scope: string, sources: [string], volatility: static | periodic | volatile}
  readme: boolean                # default true
  tests: boolean                 # default true
  rationale: [string]
  conditional_loading: [string]
  file_list:                     # the change set
    - {path: string, action: add | change | remove}
```

## Confirmation Semantics

- A confirmation is an explicit affirmation (`generate`, `proceed`, `yes`, or equivalent) of a presented change set.
- Affirmations count only while a confirmation is pending; otherwise they are ordinary input.
- Material change = any change to the file list, public I/O contract, tools, permissions, or safety controls. Material changes require reconfirmation.
- Wording, formatting, and autofix classes are not material.
- Deletion requires the change set that lists it to be confirmed; the `file_delete` `confirm` flag records that confirmation and is never independent.
- Release always requires its own confirmation (CONFIRM_RELEASE).

## Package State

```yaml
package:
  name: string
  mode: CREATE | REVIEW | REFACTOR | VALIDATE | TEST | VERSION | RELEASE
  stage: intake | brainstorm | design | confirm | generate | review | propose_changes | refactor | impact_analysis | version | validate | test | release_readiness | confirm_release | release | deliver
  status: active | blocked | release_ready | released
  package_version: string | null
  policy: object | null          # optional overrides allowed by Policy Defaults
artifacts:
  - path: string
    type: skill | agent | capability | knowledge | readme | changelog | scenarios
    version: string | null
    lifecycle: draft | validated | released | deprecated
    content_hash: string
decisions:
  - {id: string, decision: string, source: user | architect | policy, status: confirmed | pending}
open_issues:
  - {id: string, severity: critical | major | minor, description: string, status: open | resolved | deferred}
gates:
  - {name: string, scope: package | <artifact-path>, status: PASS | FAIL | BLOCKED | NOT_APPLICABLE | STALE, version: string | null, content_hash: string | null}
waivers:
  - {finding_id: string, gate: string, reason: string, approved_by: user, content_hash: string}
permitted_next_actions: [string]
```

Storage:

- State file: `<workspace>/.architect/<package-name>.state.yaml`, outside the package, never packaged.
- Without file persistence, emit the state block in the final report each turn so it is carried in conversation.

## Content State

- `content_hash`: sha256 of file bytes with CRLF normalized to LF. Package hash: sha256 of sorted `path:hash` lines over all package files.
- Versions are assigned before validation. Results are tied to the `(version, content_hash)` stored at validation time.
- Draft artifacts may change without a version bump; any content change yields a new hash and makes affected results STALE.

## Gate Vocabulary

- `PASS`: checks succeeded.
- `FAIL`: required condition failed.
- `BLOCKED`: required information, authorization, or tooling is missing.
- `NOT_APPLICABLE`: gate does not apply.
- `STALE`: prior result no longer applies to current content state.

## Gate Applicability

| Gate | Applies when |
|---|---|
| PARSE, SCHEMA, REFERENCES, CONTRACT, BEST_PRACTICES, DEPENDENCIES, CRITERIA | always |
| SAFETY | `safety_applicable` (see Policy Defaults) |
| KNOWLEDGE | any `knowledge/*.md` exists |
| README | `README.md` exists or `artifact_plan.readme` is true |
| REGRESSION | `tests/scenarios.yaml` exists or a change plan lists `tests_to_rerun` |

Overall status: FAIL if any applicable gate is FAIL; else BLOCKED if any is BLOCKED; else STALE if any is STALE; else PASS. NOT_APPLICABLE only when no gate applies.

## Severity

`critical` and `major` findings make their gate FAIL. `minor` findings leave it PASS with a note. "Material" is used only for changes (see Confirmation Semantics), never for findings.

## Error Taxonomy

```text
INPUT_ERROR
CONFIGURATION_ERROR
DEPENDENCY_ERROR
REFERENCE_ERROR
LOGIC_ERROR
VALIDATION_ERROR
DATA_QUALITY_ERROR
SECURITY_ERROR
AUTHORIZATION_ERROR
ENVIRONMENT_ERROR
USER_ACTION_REQUIRED
```

Every error token used in any artifact MUST be in this list.

## Lifecycle

`draft → validated → released → deprecated`. Tracked in Package State. Released artifacts are immutable; change means a new version.

# Policies

- Strict YAML loader; no anchors, aliases, or custom tags.
- Required fields and headings must exist. SemVer must parse. Relative references must resolve.
- JSON tool schemas, when shipped, use `additionalProperties: false`.
- Any artifact change invalidates affected validation results.
- Runtime state is not domain knowledge. Package state is architect-side control data.

## Policy Defaults

| Policy | Default |
|---|---|
| required gates | every applicable gate (see Gate Applicability) |
| release_ready | every applicable gate PASS at the current content_hash, AND no open critical/major issue without waiver, AND `CHANGELOG.md` has an entry for the package version and every artifact version, AND no blocking deprecated dependency |
| package_version | previous version bumped by the highest change class among changed artifacts; initial `0.1.0`; components version independently |
| deprecated_dependency | block for new dependencies, warn for existing |
| safety_applicable | regulated/sensitive-data domain, external-content consumption, any tool with side_effects `irreversible` or `high_impact`, or a high-impact action |
| autofix classes | `frontmatter_format`, `heading_name`, `broken_relative_path`, `readme_inventory_drift`; one cycle, file list unchanged, reported to the user |
| waivable findings | minor and major findings outside the SAFETY gate; not waivable: critical findings, SAFETY, PARSE, REFERENCES |

`package.policy` MAY override only `package_version` and `deprecated_dependency`.

Waivers: a waiver records finding id, reason, and user approval, and is tied to a content_hash. Waived findings are excluded from gate status but listed in the report. A content change makes the waiver STALE.

# Guidance

Validation order:

1. Parse frontmatter.
2. Validate allowed fields.
3. Validate type and SemVer.
4. Validate required headings.
5. Validate structured I/O and tool contracts when present.
6. Resolve references.
7. Validate the dependency graph.
8. Validate knowledge metadata when applicable.
9. Record exact artifact state for validation.
10. Apply lifecycle and gate rules.

`scripts/validate.py` performs the deterministic parts of steps 1-9.

# Provenance

Source: agent-architect architecture revision, 2026-10-01. Authority: internal standard, tier 4. Review: quarterly.
