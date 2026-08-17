---
name: adrlane-workspace-routing
description: >-
  Use when `.adrlane/workspace.yaml` exists at the workspace root and documentation
  may belong at project level (`docs/`) or in a sub-repository (`<repo>/docs/`).
  Routes adrlane-write-* skills to the correct docs tree automatically.
---

# Workspace documentation routing (adrlane)

## Activation

Apply this skill only when `.adrlane/workspace.yaml` exists at the **Cursor workspace root**.
If it is missing, use the standard single-repo adrlane skills unchanged.

## Configuration

Read `.adrlane/workspace.yaml` at the workspace root:

| Key | Default | Meaning |
| --- | --- | --- |
| `project_docs` | `docs` | Cross-cutting docs at workspace root |
| `repo_roots` | *(empty)* | Optional grouping folders to scan for repositories |

### Finding service repositories

A **service repository** is a directory with `docs/llm/AGENT_PROTOCOL.md`
(bootstrapped with `adrlane init`).

**Flat layout** (repos at project root) — omit `repo_roots` or leave it empty:

```
project/
  docs/              ← project-level (from project_docs)
  repository1/docs/
  repository2/docs/
```

Scan **immediate children** of the workspace root. Skip `project_docs`, dot-directories
(`.adrlane`, `.cursor`, …), and other non-repo folders.

**Grouped layout** — set `repo_roots` to parent folders:

```
project/
  docs/
  services/order-service/docs/
  frontends/checkout-fe/docs/
```

```yaml
repo_roots:
  - services
  - frontends
```

Scan **immediate children** of each `repo_roots` entry.

## Routing rules

### Project scope → `{project_docs}/`

Write here when the change affects:

- multiple repositories or shared platform concerns
- workspace orchestration (compose, justfile, mr/mu config)
- cross-cutting architecture or conventions

### Service scope → `{repo}/docs/`

Write here when the change affects:

- one bounded context (API, behavior, internals of a single service, frontend, or lib)
- files under a specific sub-repository

**Resolve the repo from context:**

1. Files being edited or discussed under `{repo}/` → use that repo's `docs/`
2. User names a service explicitly → use that repo
3. Multiple repos in one artifact → prefer project scope with links to each service doc

If scope is ambiguous, ask once before writing.

## Using with other adrlane skills

When `adrlane-write-adr`, `adrlane-write-spec`, `adrlane-write-plan`, or
`adrlane-write-idea` applies:

1. Resolve scope and target prefix with this skill first.
2. Write under `{target}/adr/`, `{target}/specs/`, etc. instead of bare `docs/`.
3. Read `DECISION_RULES` and templates from the **target** tree (`{target}/llm/`).
   If a service repo lacks templates, fall back to `{project_docs}/llm/`.
4. Link across levels in `## Related` (e.g. project ADR ↔ service spec).

Never delete or skip project-level docs when adding service-level docs.

## Bootstrap reminder

Run `adrlane init --workspace` at the workspace root, and `adrlane init` in each
sub-repository that should own service-level docs.
