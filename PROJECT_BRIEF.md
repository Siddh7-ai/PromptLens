# Project Brief: AI Agent Compression Proxy

Read `PROJECT_BRIEF.md` for context before starting.

## What we're building

A local compression proxy for AI coding agents. It sits between an agent (e.g. Claude Code)
and the LLM API, compresses tool-call outputs (JSON, logs, stack traces, file contents)
before forwarding them, and exposes a retrieve_original(id) tool so the model can recover
the full data if it needs it. Goal: cut token usage 50-80% with no loss of correctness.

## Non-negotiable constraints

* Rule-based compression only. No training or fine-tuning a model.
* Every compression must be reversible via a retrieval store (hash-keyed, TTL-based).
* Must work as a transparent proxy — zero code changes required in the agent being wrapped.
* Python + FastAPI. Token counting via tiktoken.
* Scope is locked to ONE agent integration and TWO content types (JSON, text/logs).
* Do not add AST code compression, ML models, or extra agent support unless explicitly asked.

## Definition of done for the whole project

* `compress()` function with unit tests passing on a fixture set of real tool outputs
* Working FastAPI proxy that intercepts, compresses, and forwards Anthropic-format requests
* Retrieval round-trip proven correct in tests
* A real agent completing a real coding task through the proxy, with measured token savings
* A results table: baseline tokens vs compressed tokens vs answer-correctness, across 5+ tasks
* A dashboard/endpoint showing live savings
* README that gets a stranger from git clone to a working demo in under 5 minutes

## How to work with me on this

* I am the reviewer. After each mission, summarize what changed, show me the test output, and wait for my go-ahead before starting the next mission.
* If a task is ambiguous, ask me — don't assume and build the wrong thing.
* Never mark a mission "done" without a runnable test or demo proving it works.
* Keep changes scoped to the current mission. Don't refactor unrelated code without asking.

## Mission Sequence

1. **Mission 1 — Fixtures + token counting baseline** (CURRENT)
2. **Mission 2 — JSON compression**
3. **Mission 3 — Text/log compression**
4. **Mission 4 — Retrieval store**
5. **Mission 5 — FastAPI passthrough proxy**
6. **Mission 6 — Wire compression into the proxy**
7. **Mission 7 — Real agent integration**
8. **Mission 8 — Benchmarking + dashboard**
9. **Mission 9 — README + polish**
