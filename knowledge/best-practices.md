---
name: best-practices
type: knowledge
version: 0.1.0
description: Architecture and authoring principles for reliable, composable, efficient LLM skill packages, with yes/no checklists for the semantic gates.
triggers:
  - artifact authoring
  - review
  - refactor
  - validation
inputs:
  - artifact or package under construction
outputs:
  - applicable design principles
  - checklist results
dependencies:
  - knowledge/schemas.md
knowledge_class: static
---

# Facts

## Architecture

- One skill = one coherent job. One capability = one reusable job.
- Separate behavior, runtime knowledge, state, and human documentation. Parameters are declared in skill `Inputs`.
- Prefer the minimum sufficient artifact set.
- Prefer explicit contracts over prose assumptions; make dependencies and boundaries visible.
- Make behavior testable with scenarios (`knowledge/schemas.md`, Scenario Format).

## Contract-First

Define, as applicable: triggers, non-triggers, inputs, outputs, constraints, dependencies, failure modes, tools, permissions, side effects, authorization, and recovery/escalation. Use structured schemas when labels are insufficient for composition.

## Skills

- Define when to use and when not to use.
- Use explicit decision points; define ambiguity, missing-data, tool-failure, and recovery behavior.
- Define tool calls, trust boundaries, and output format.
- Cover adversarial/failure inputs when relevant.
- Do not embed reusable/volatile knowledge.

## Capabilities

- One job, explicit scope and non-goals, explicit dependencies.
- Tool/data/permission mapping; enumerated failures and recovery.
- Composition/handoff behavior; human escalation where needed.

## Knowledge

- Atomic entries; facts, policies, and guidance separated.
- Source, authority, scope, freshness, and effective period tracked for managed knowledge.
- Conflicts resolved by proposition-specific authority.
- Runtime state is not knowledge.

## Separation

Keep small stable procedure-intrinsic facts inline. Externalize reusable, volatile, provenance-sensitive, access-controlled, or large knowledge. Keep lifecycle state separate.

## LLM Optimization

- Imperative and token-dense; machine-readable contracts first.
- Load only applicable knowledge.
- Reference shared rules rather than duplicating them.
- Minimal examples; counterexamples only where useful.
- Prefer deterministic checks over prose self-checks.

## Token Tradeoff

Externalization saves repeated prompt tokens but can add retrieval latency, failure risk, fragmentation, and reference complexity. Do not externalize trivial stable information for purity.

## Observability

Where infrastructure supports it, lifecycle mutations should record timestamp, operation, artifact/package, version, result, and confirmation state.

## Checklist: BEST_PRACTICES

Answer each applicable item yes/no with evidence. A "no" on a major item is a major finding.

| Id | Check | Severity |
|---|---|---|
| BP-01 | The skill states when to use it and when not to (`triggers`, `non_triggers`). | major |
| BP-02 | The skill has one coherent job; each capability has one job and stated non-goals. | major |
| BP-03 | Decision points are explicit. | major |
| BP-04 | Ambiguity, missing-data, and tool-failure behavior are defined. | major |
| BP-05 | Output format is defined. | major |
| BP-06 | Material behavior is covered by scenarios meeting the minimum set. | major |
| BP-07 | Reusable or volatile knowledge is externalized; small stable facts are local. | minor |
| BP-08 | Shared rules are referenced, not duplicated. | minor |
| BP-09 | No assumption contradicts `target_llm`. | minor |

## Checklist: CONTRACT

| Id | Check | Severity |
|---|---|---|
| CT-01 | No trigger overlaps a `non_trigger`. | major |
| CT-02 | Every declared input is used and every declared output is produced. | major |
| CT-03 | Every declared tool has a Tool Contract and is used. | major |
| CT-04 | Permissions are the minimum needed. | major |
| CT-05 | Each failure mode maps to the taxonomy with a recovery or escalation. | major |
| CT-06 | No cyclic capability handoffs. | major |

# Policies

- Critical and major checklist failures cause validation failure; minor failures are notes.
- User criteria are not silently reinterpreted.

# Guidance

1. Load applicable principles.
2. Select the minimum sufficient artifacts.
3. Author explicit contracts.
4. Validate structure, references, dependencies, safety, and criteria.
5. Test changed behavior.
6. Revalidate after changes.

# Provenance

Source: agent-architect architecture revision, 2026-10-01. Authority: internal standard, tier 4. Review: quarterly.
