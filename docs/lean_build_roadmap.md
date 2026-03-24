# Lean Build Roadmap

## Goal

Turn Project Messiah from a speculative system into a measured product.

The first version should answer one question:

**Can we make high-quality, mergeable code contributions with positive unit economics?**

Everything else is secondary.

## What we are not building first

These are deferred until the core loop works:

- GraphRAG / Memgraph
- ERC-8004 identity
- Chain-based reputation integrations
- x402 monetization layer
- PySide6 desktop dashboard
- ZK proofs
- TEE infrastructure
- multi-account scaling

## Phase 0: Prove the core loop

### Deliverable

A local-only agent that:

1. ingests candidate tasks,
2. scores them,
3. generates a patch plan,
4. runs QA,
5. outputs a submission bundle in dry-run mode.

### Success criteria

- We can run the pipeline end to end on sample tasks.
- We can inspect every decision the agent makes.
- The system produces artifacts a human can approve before any live submission.

### Why this comes first

Because it tests the only thing that matters initially: output quality.

## Phase 1: Real contribution engine

### Deliverable

A real but conservative contributor that only works on pre-approved tasks and never auto-submits without a human gate.

### Success criteria

- At least 3 serious candidate patches generated on real issues
- At least 1 real merged contribution
- Measured cost per attempt
- Measured acceptance rate

### Non-goals

- no autonomous mass submissions
- no bounty-platform expansion
- no security contest automation

## Phase 2: Thin operations layer

### Deliverable

A simple backend plus database for tracking runs, tasks, costs, outcomes, and review notes.

### Success criteria

- every run is logged,
- every task has a lifecycle state,
- we can compute acceptance rate and cost per merged PR.

### Note

Supabase can be added here if we still want it after Phase 1. It should not block the first working system.

## Phase 3: Monetization experiments

### Deliverable

One paid endpoint, not five.

The endpoint should expose the single most reusable internal capability, for example:

- repo context pack generation,
- patch review / QA,
- or issue feasibility scoring.

### Success criteria

- at least 1 external user,
- at least 10 paid calls,
- evidence that buyers return voluntarily.

If no one pays for one service, there is no reason to build a bazaar of services.

## Phase 4: Trust and expansion

Only after the core loop and one monetization path work should we consider:

- x402 expansion,
- identity / attestation,
- stronger reputation systems,
- platform-specific routing,
- and security-bounty adjacent work.

## Proposed first codebase

We should keep the first implementation small and inspectable.

### Initial stack

- Python 3.12+
- CLI first
- local JSON or SQLite for Phase 0
- pytest for tests
- Ruff for linting

### First folders

- `docs/` for decisions and operating notes
- `src/messiah/` for application code
- `tests/` for behavior tests
- `fixtures/` for sample tasks and repo snapshots

## Initial file plan

These are the first files worth writing together:

1. `pyproject.toml`
2. `README.md`
3. `src/messiah/config.py`
4. `src/messiah/models.py`
5. `src/messiah/task_loader.py`
6. `src/messiah/scorer.py`
7. `src/messiah/planner.py`
8. `src/messiah/qa.py`
9. `src/messiah/pipeline.py`
10. `src/messiah/cli.py`
11. `tests/test_scorer.py`
12. `tests/test_pipeline.py`

## What each first file does

### `pyproject.toml`

Defines package metadata, dependencies, linting, and test commands.

### `README.md`

States the exact scope of the MVP and how to run it.

### `src/messiah/config.py`

Loads environment variables and runtime settings.

### `src/messiah/models.py`

Defines typed data structures for tasks, scores, plans, patches, and outcomes.

### `src/messiah/task_loader.py`

Loads candidate tasks from local fixture files or later APIs.

### `src/messiah/scorer.py`

Ranks tasks by expected value, complexity, confidence, and competition.

### `src/messiah/planner.py`

Converts a chosen task into a structured implementation plan.

### `src/messiah/qa.py`

Runs validation checks and produces a pass/fail report.

### `src/messiah/pipeline.py`

Coordinates the flow from task intake to dry-run submission bundle.

### `src/messiah/cli.py`

Provides the local command-line entry point.

### Tests

Prove the scoring logic and pipeline behavior before we add more surface area.

## Build order recommendation

We should write the files in this order:

1. `pyproject.toml`
2. `README.md`
3. `src/messiah/models.py`
4. `src/messiah/config.py`
5. `src/messiah/task_loader.py`
6. `src/messiah/scorer.py`
7. `src/messiah/planner.py`
8. `src/messiah/qa.py`
9. `src/messiah/pipeline.py`
10. `src/messiah/cli.py`
11. tests

This gives us a runnable dry-run core before we touch infra.
