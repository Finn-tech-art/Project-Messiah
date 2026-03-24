# Project Messiah

Project Messiah is a delivery engine for small, high-value, clearly scoped jobs.

The goal is not to be a fully autonomous bounty empire. The goal is to help sell and deliver tightly scoped work with high acceptance probability and clear proof of completion.

The system is designed around:

- LangGraph for orchestration
- Groq for fast inference
- PySide6 for the local operator dashboard

## What it is

- a system for qualifying inbound jobs
- a scoring engine for scope, confidence, and likely margin
- a planner that turns approved jobs into an execution checklist
- a delivery formatter that produces buyer-facing output
- a metrics layer for tracking win rate, turnaround time, and margin
- a local dashboard for human review and approvals

## What it is not

- a general autonomous agent that works on anything
- a spammy open-source bounty bot
- a security-audit platform
- a crypto trading engine
- a no-human-in-the-loop delivery system

## First offers

These are the first offers this codebase is designed to support:

1. Bug Rescue
2. Codebase Health Audit
3. CI / Deployment Recovery
4. Automation Sprint
5. AI Output QA
6. Research Brief Sprint
7. Data Cleanup Sprint
8. Content System Pack

## MVP workflow

The first version runs locally in dry-run mode.

1. Load a job brief from JSON.
2. Qualify the job and identify its service line.
3. Estimate difficulty, confidence, and price band.
4. Build an execution plan.
5. Generate a delivery checklist.

## Initial repo structure

```text
docs/
fixtures/
src/
  messiah/
tests/
```

## Development status

Current phase: commercial MVP definition

Current priority:

- define typed job models
- define service lines and qualification rules
- wire the LangGraph workflow
- keep the PySide6 dashboard in the architecture
- implement qualification rules
- implement estimation rules
- produce a dry-run pipeline

## Roadmap

1. Build the local dry-run engine.
2. Test it on sample jobs.
3. Use it to support productized offers across technical, research, ops, and content marketplaces.
4. Add metrics and evidence capture.
5. Add one reusable paid API only after service demand is real.
