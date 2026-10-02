---
name: brainstorm
type: capability
version: 0.1.0
description: Generic, skill-agnostic requirements elicitation. Classifies depth (quick, standard, deep), asks one question per turn, writes understanding back for correction, and returns a structured brief without writing files.
triggers:
  - skill requires requirements elicitation
  - design ambiguity detected
  - user requests brainstorming
inputs:
  - topic
  - brief_schema
  - prior_answers
  - constraints
  - depth_hint
  - max_rounds
outputs:
  - brief
  - open_questions
  - assumptions
  - user_stated
  - flags
  - depth
  - rounds_completed
  - stopped_by
dependencies:
  - knowledge/schemas.md
optional_dependencies:
  - knowledge/safety-policies.md
---

# Purpose

Converge on a structured brief sufficient for downstream work without further clarification. Scale elicitation depth to task complexity and announce the depth so the caller can override it.

# Scope

In scope: requirements, ambiguity, assumptions, contradictions, acceptance criteria, scope assessment, decomposition flagging, safety/authorization questions.

Out of scope: artifact generation, validation, versioning, execution, file writes, invoking downstream capabilities. This capability returns a brief; the caller decides what happens next.

# Inputs

```yaml
topic: string
brief_schema: object      # caller-defined; default is Design Brief in knowledge/schemas.md
prior_answers: object     # optional; for resumed sessions
constraints: [string]     # optional
depth_hint: quick | standard | deep   # optional; classified from the topic if absent
max_rounds: integer       # optional; defaults by depth (quick 2, standard 4, deep 8)
```

A round is one question and its answer. The write-back is not a round. When `brief_schema` has its own `open_questions` or `assumptions` fields, they mirror the top-level outputs of the same name; fill both from one source.

# Outputs

```yaml
brief: object             # conforms to brief_schema
open_questions: [string]
assumptions: [string]     # inferred, not user-stated
user_stated: [string]     # explicitly said by the user
flags: [string]           # decomposition_needed | unresolved_conflict | schema_fallback | scope_overflow
depth: quick | standard | deep
rounds_completed: integer
stopped_by: user | max_rounds | sufficient
```

# Dependencies

- `knowledge/schemas.md`
- `knowledge/safety-policies.md` (optional)

# Rules

## Depth

Announce the depth on its own line before the first question.

| Depth | When | Rounds | Behavior |
|---|---|---|---|
| quick | Intent is already supplied or a confirmation; every required field is answerable from context | 0-2 | Write-back may be the only step |
| standard | Well-scoped task with clear boundaries (default) | 2-4 | Targeted questions, write-back, brief |
| deep | Novel problem space, several stakeholders, ambiguous success criteria, or user asks for thoroughness | up to 8 | Sectioned questions; propose 2-3 approaches with trade-offs before the write-back |

- Use `depth_hint` unless the topic contradicts it; then surface the conflict and take the heavier depth.
- A topic naming several independent subsystems is `deep` and goes through the Decomposition Check first.
- Ratchet: hidden complexity found mid-session raises depth (quick → standard → deep) and is announced. Depth never drops mid-session; only a stop signal ends early. A ratchet raises the default round cap to the new depth's, but never overrides an explicit `max_rounds`.

## Questions

- One question per turn. Prefer multiple choice; use open-ended only when options cannot be listed.
- Ask only what is needed to fill an empty required field or change the artifact plan. Do not probe for features the user has not signalled (YAGNI).
- Never repeat an answered question unless clarification is required.
- Elicit `acceptance_criteria` with one question when absent. Never invent them.
- Surface contradictions; never silently resolve them. Ask one resolution question; if still unresolved, stop with `flags: [unresolved_conflict]` and the conflict in `open_questions`.
- Keep `user_stated` and `assumptions` separate.

## Decomposition Check

If the topic is too large for one brief, set `decomposition_needed`, name the independent pieces, and offer to brainstorm the first piece through the normal flow. Do not refine details of an oversized topic first.

## Write-back

When required fields are filled, summarize (a) what the user stated, (b) what is assumed, (c) what remains open, and invite correction. The brief is formed only after the user corrects it or confirms it.

## Stop conditions

Stop on the first of:

- `sufficient`: all required fields are filled, no open question could change the artifact plan, and the write-back is acknowledged.
- `max_rounds` for the current depth.
- `user`: `stop brainstorm`, `skip`, or `enough`. Empty required fields become `open_questions` and block DESIGN. `pause` follows Package State storage in `knowledge/schemas.md`.

Tokens `proceed` and `generate` never stop brainstorming; they belong to the caller's CONFIRM stage. A `yes` or "that's right" answering a pending write-back acknowledges the write-back only; it is not a confirmation of a change set.

## Gates

- HARD-GATE, handoff: emit no brief until the write-back is acknowledged, a stop signal arrives, or the user declines to resolve a contradiction. In the last two cases emit the brief with `open_questions` filled and `stopped_by: user`. Reaching `max_rounds` still requires the write-back first.
- HARD-GATE, no downstream action: emitting the brief is the terminal state. Write no files, invoke no capability, and treat the brief as no approval of anything.

## Anti-Patterns

| Thought | Reality |
|---|---|
| "The topic is obvious; skip the depth announcement." | The caller may know context you lack. Announce it. |
| "Ask everything at once to save rounds." | One question per turn. Batches produce shallow answers. |
| "They already stated the purpose; skip the write-back." | Write-back exposes assumptions and prevents drift. |
| "This feels too heavy; quietly drop to a lighter depth." | The ratchet is one-way. |
| "This is really two projects, but I'll push on." | Run the Decomposition Check first. |
| "The brief is done, so I can start building." | A brief is not approval. Emit it and stop. |
| "They said `generate`, so I'll stop brainstorming." | That token belongs to the caller's CONFIRM stage. |
| "I'll add a feature they'd probably want." | YAGNI. Probe only what the user signalled. |

## Flow

```text
CLASSIFY depth → (several subsystems? flag decomposition_needed, DECOMPOSE) → ANNOUNCE depth
→ LOOP until stop: ASK one question → RECORD → (hidden complexity? RATCHET and announce)
→ WRITE-BACK → AWAIT acknowledgement or correction → EMIT brief, stopped_by, flags → STOP
```

# Failure Modes

- `INPUT_ERROR`: missing topic, or invalid `brief_schema` (fall back to Design Brief and set `schema_fallback`).
- `LOGIC_ERROR`: contradiction unresolved after one resolution question.
- `USER_ACTION_REQUIRED`: required decision or acceptance criteria missing, or the user refuses all questions (emit the brief with `assumptions` filled and `stopped_by: user`).
- `SECURITY_ERROR`: unsafe scope.
- `AUTHORIZATION_ERROR`: high-impact scope lacks an authorized actor.

# Error Handling & Safety

Do not solicit or store secrets, credentials, or raw sensitive identifiers; ask for placeholder references. When `safety_applicable` (see Policy Defaults in `knowledge/schemas.md`), load `knowledge/safety-policies.md`, ask its safety questions, and fill `safety_requirements` in the brief. Escalate repeated contradictions or unsafe scope. Do not persist brief content outside the caller's context without explicit instruction.
