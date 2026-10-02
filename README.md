# agent-architect

## Purpose

Contract-driven skill for designing, generating, reviewing, refactoring, validating, testing, versioning, and releasing LLM skill packages.

## Quick Start

1. Describe the skill or package change.
2. Answer brainstorming questions one at a time, including how you will judge success, then correct the recap of what was understood (`stop brainstorm` or `skip` ends it early).
3. Review the design plan: artifact plan, file list, assumptions, and open questions.
4. Confirm with `generate`, `proceed`, or `yes`. Confirmation only counts after a plan is presented.
5. The skill writes only the confirmed files inside the designated package path.
6. Validation and scenario tests run; the package ends at `release_ready`.
7. Release is a separate request and needs its own confirmation.
8. The skill reports file versions, gate results, tests, and remaining findings.

A material change to the file list, public I/O contract, tools, permissions, or safety controls requires reconfirmation.

## Inputs and Outputs

Inputs: a natural language design request, existing package files, and acceptance criteria (never invented).

Outputs: `skill.md`, optional `capabilities/` and `knowledge/`, `tests/scenarios.yaml`, `README.md`, and `CHANGELOG.md` in the target package, plus a final report. Package state is kept outside the package in `.architect/<name>.state.yaml`, or carried in the conversation when files are unavailable.

## Architecture

```text
skill.md
  ↓
capabilities/
  ↓
knowledge/
  ↓
generated package
  ├── skill.md
  ├── capabilities/
  ├── knowledge/
  ├── tests/scenarios.yaml
  ├── README.md
  └── CHANGELOG.md
```

Package state is architect-side control data and is not injected into runtime prompts.

## Validation

Applicable gates are `PARSE`, `SCHEMA`, `REFERENCES`, `CONTRACT`, `BEST_PRACTICES`, `SAFETY`, `KNOWLEDGE`, `DEPENDENCIES`, `README`, `CRITERIA`, and `REGRESSION`. Status is `PASS | FAIL | BLOCKED | NOT_APPLICABLE | STALE`.

Every applicable gate must be `PASS` at the current content state, with no open critical or major issue, before release. Gate applicability, severity, and release readiness are defined in `knowledge/schemas.md`.

`scripts/validate.py <package-root>` runs the deterministic checks. `validate.py --file <artifact.md>` checks a single artifact.

## Capabilities

| Capability | Description | Version |
|---|---|---:|
| brainstorm | Depth-classified elicitation, one question per turn, write-back before the brief. | 0.1.0 |
| recommend-artifacts | Selects the minimum sufficient artifact set and file list. | 0.1.0 |
| design-skill | Authors the skill behavior contract. | 0.1.0 |
| design-capability | Authors a reusable capability contract. | 0.1.0 |
| design-knowledge | Authors provenance-aware runtime knowledge. | 0.1.0 |
| design-readme | Generates the human-facing package README. | 0.1.0 |
| validate-artifacts | Runs structural, integrity, safety, and criteria gates (read-only). | 0.1.0 |
| test-artifacts | Authors and runs regression scenarios. | 0.1.0 |
| review-refactor | Reviews and safely applies confirmed refactors and autofixes. | 0.1.0 |
| manage-version | Handles SemVer, changelog, deprecation, release readiness, and release. | 0.1.0 |

## Limitations

- Static validation and static scenarios do not prove runtime correctness.
- Runtime testing depends on available execution infrastructure.
- External facts require source, authority, scope, and freshness evaluation.
- High-impact or regulated behavior may require additional human or domain review.
- No separate configuration artifact; parameters are declared in skill `Inputs`.
- Non-goals: multi-skill packages with shared knowledge, and migration from earlier schema versions.

## Files

- `SKILL.md` — skill behavior, lifecycle, tool contracts, and safety.
- `capabilities/` — reusable operations, one file each.
- `knowledge/` — schemas, best practices, safety policies, and authority rules.
- `scripts/validate.py` — deterministic validation checks.
- `tests/scenarios.yaml` — regression scenarios for this package.
- `examples/meeting-summary-skill.md` — golden example of a conforming skill.
- `README.md` — this guide.
- `CHANGELOG.md` — version history.
