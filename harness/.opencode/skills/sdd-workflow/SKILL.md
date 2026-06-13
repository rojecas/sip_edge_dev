---
name: sdd-workflow
description: >
  Spec Driven Development workflow for this project. Use ONLY when working on
  a feature with "sdd": true in feature_list.json. Follows the exact pipeline:
  pending -> spec-author -> spec_ready -> human approval -> in_progress ->
  implementer -> reviewer -> done. Automatically reads init.ps1, AGENTS.md,
  and docs/specs.md for full workflow details.
---

# SDD Workflow — Harness-SDD

## Pipeline

```
pending → [spec-author] → spec_ready → ⏸ HUMAN → in_progress → [implementer → reviewer] → done
```

## Roles

| Agent | Tool | Responsibility |
|-------|------|---------------|
| `leader` | primary | Orchestrator. Reads `feature_list.json`, delegates to sub-agents. NEVER writes code. |
| `spec-author` | subagent | Writes `specs/<name>/{requirements,design,tasks}.md`. NEVER writes code. |
| `implementer` | subagent | Writes code + tests per `tasks.md`. Verifies with `init.ps1`. |
| `reviewer` | subagent | Validates traceability (R<n> ↔ tests), tasks completeness, CHECKPOINTS. |

## Trigger

When a user says "implement the next feature" or similar:
1. Read `feature_list.json`
2. Find the first `pending` feature with `"sdd": true`
3. Follow the Caso A → B → C logic from `leader.md`

## Key files

- `feature_list.json` — source of truth for feature status
- `AGENTS.md` — navigation map
- `docs/specs.md` — EARS notation and spec format rules
- `CHECKPOINTS.md` — objective evaluation criteria
- `init.ps1` — verification script (must pass before closing)
