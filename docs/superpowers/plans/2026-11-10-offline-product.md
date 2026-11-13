# GPU Cost Optimizer Offline Product Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an installable, transparent offline estimator through the existing CLI and a usable static browser calculator.

**Architecture:** Keep the Python package as the canonical heuristic model and add a dependency-free browser calculator that mirrors the model. Browser/Python fixtures, CLI serialization tests, and local smoke checks prevent silent drift.

**Tech Stack:** Python 3.9+, Click, pytest, semantic HTML, CSS, vanilla JavaScript, Node built-in test runner for browser calculation parity.

**Spec:** `docs/specs/2026-11-10-gpu-cost-optimizer/`

## Global Constraints

- Python 3.9+ and existing `gpuopt` commands remain supported.
- Static web app runs without network, server, third-party script, or account.
- Simulation and historical price references are clearly labeled; never claim live prices or measured GPU performance.
- Workflow JSON is data only and is never executed.
- Use canon colors #05030a, #ff073a, #d4af37, #4de8e0 and honor accessibility requirements.

## Review Focus

- Malformed JSON and non-object workflow input show actionable errors rather than tracebacks.
- Boundary numeric values are rejected before costly arithmetic or rendering.
- An unsupported GPU or insufficient VRAM is never surfaced as a valid recommendation.
- Imported custom fields survive form editing and workflow export.
- Browser model output stays aligned with Python on included canonical fixtures.

---

### Task 1: Harden workflow loading and add report JSON

**Files:**
- Modify: `optimizer/profiler.py`
- Modify: `optimizer/report.py`
- Modify: `optimizer/cli.py`
- Test: `tests/test_cli_regressions.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Produce `report_to_dict(report) -> dict[str, object]` with stable model/tariff provenance and JSON-safe bottleneck/optimization fields.
- Preserve Markdown as the default `report` format; add `--format markdown|json`.

- [ ] Add tests that malformed JSON, invalid top-level types, and invalid workflow fields yield concise Click errors.
- [ ] Add JSON report tests for deterministic keys, disclaimer, and parseability.
- [ ] Run focused tests and confirm the new expectations fail.
- [ ] Implement error translation and report serialization with no internal workflow objects in output.
- [ ] Run focused tests and confirm they pass.

### Task 2: Build testable browser calculation core

**Files:**
- Create: `docs/calculator.js`
- Create: `tests/web-model.test.cjs`
- Test: `optimizer/profiler.py`, `optimizer/pricing.py` fixtures

**Interfaces:**
- Export CommonJS-compatible pure functions `validateWorkflow(workflow)`, `profileWorkflow(workflow, gpu)`, `compareGpus(workflow)`, and `buildResult(workflow, selectedGpu)` for browser and Node test use.
- Profile object keys: `workflow_name`, `gpu`, `steps`, `total_seconds`, `vram_estimate_gb`.
- Comparison rows include GPU id, historical hourly price, simulated seconds, estimated cost, VRAM capacity, estimated VRAM, and feasibility.

- [ ] Add Node built-in tests for canonical fixture parity, unknown GPU, invalid bounds, and infeasible GPU rows.
- [ ] Run `node --test tests/web-model.test.cjs` and confirm expected failures before implementation.
- [ ] Implement the pure deterministic model mirroring Python's formulas and GPU table.
- [ ] Run Node tests and compare outputs against Python CLI/module values for fixtures.

### Task 3: Deliver the accessible static calculator

**Files:**
- Modify: `docs/index.html`
- Modify: `docs/site.css`
- Modify: `docs/site.js`
- Modify: `docs/calculator.js`
- Create: `examples/web-parity.json`

**Interfaces:**
- Inputs use existing workflow JSON keys: name, pipeline, model, scheduler.type, scheduler.steps, resolution, batch_size, safety_checker.
- UI actions: load sample, import JSON, calculate, download workflow JSON, download result JSON.
- Opt-in draft state uses localStorage key `gpuopt.workflow.v1`; saved data can be cleared and errors render in a live region.

- [ ] Add UI acceptance coverage for initial empty state, invalid import, valid estimate, feasibility labels, and exports.
- [ ] Verify tests fail against the current generic page.
- [ ] Replace generic marketing-only markup with the estimator and a concise methodology section.
- [ ] Add responsive styles, keyboard focus, 44px targets, and reduced-motion support.
- [ ] Connect imports, sample workflow, calculation, comparisons, local draft, and JSON downloads.
- [ ] Run automated tests and inspect the page at mobile and desktop widths.

### Task 4: Adoption and deliverable documentation

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml` if required for package correctness
- Modify: `.github/workflows/ci.yml` only if new checks need to run in CI
- Test: packaging and documented CLI smoke commands

- [ ] Document browser calculator, CLI installation/use, model limits, historical price status, and exports.
- [ ] Verify package build/install in the available Python environment.
- [ ] Run compile, full pytest suite, CLI help, sample profile, GPU list, and Markdown/JSON report smoke commands.
- [ ] Run HTML/JS checks available in the repo and inspect `git diff --check` and `git status`.
- [ ] Record actual command output, exit codes, and any environment limitation.
