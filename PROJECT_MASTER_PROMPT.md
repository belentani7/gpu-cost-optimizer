# PROJECT MASTER PROMPT — GPU Cost Optimizer

> Canonical repository: `belentani7/gpu-cost-optimizer`.
> Product: **GPU Cost Optimizer**. Promise: *Modelar antes de gastar.*
> Category: developer tooling / offline estimation — not an actual GPU benchmark or a live cloud-pricing service.

## Identity and product boundary

The project estimates costs, duration, memory requirements, and possible optimizations of AI diffusion workflows **without running GPU workloads**. Its main value is an explainable decision aid, not unverifiable promises of savings. Historical built-in hourly tariffs must always be described as historical and nonbinding; never present them as real-time prices or production quotes. Do not split this product into new repositories or transplant unrelated artistic/educational product ideas here.

## Existing foundations

Python package in `optimizer/`, command line entry point `gpuopt`, examples, pytest tests, reference docs and static landing page in `docs/`. The main surfaces are `profile`, `compare`, `recommend`, `optimize`, `report`, and `list-gpus`. Current pricing is historical, timing and VRAM are simulations, and scheduler changes may affect output quality.

Read the actual modules and tests before changes. Preserve the Python package/CLI architecture, offline operation, transparent model assumptions, existing sample workflow files, and compatibility with Python 3.9+.

## Maximum useful product vision

1. Reliable and secure workflow input: schema/versioning, bounded numeric values, clear errors, no execution of untrusted workflow content.
2. Explainable cost estimates: per-stage duration, confidence/assumption metadata, VRAM feasibility, model and resolution sensitivities, clear distinction between approximate simulation and measurements.
3. Provider-aware configurable prices: retain historical built-in references, allow timestamped explicit user-supplied tariff catalogs, and display provider, currency, compute instance, effective date and charging granularity.
4. Conservative optimization: do not degrade resolution, change precision/scheduler, or increase image dimensions unnecessarily; preserve user quality constraints by default. Show expected trade-offs and compatibility caveats.
5. Workflow comparison: baseline vs candidates with reproducible inputs, feasibility filters, cost/latency/quality axes, honest Pareto trade-offs and budget warnings.
6. Useful delivery: production-grade CLI with consistent errors; machine-readable JSON and Markdown reports; installable package; documented integration points; functional static site without false live data.
7. Real confidence: unit, property/regression and CLI integration tests, packaging tests on supported Python versions, no-secrets CI; do not call CI passing unless a runner actually executed it.

## Execution phases

- **A. Deterministic integrity**: preserve valid inputs, reject malformed data and unreasonable budgets, fix geometry and cost-selection bugs, expand regression cases.
- **B. Precision and evidence**: clear heuristic model, explicit provenance and calibration points, meaningful sensitivity ranges, no invented benchmark claims.
- **C. Price sources**: optionally import user-owned current rates with validation and timestamps. Never silently scrape or imply current prices.
- **D. Reporting and adoption**: export JSON and Markdown, useful reproducible comparisons, responsive static site and complete examples.
- **E. Validation and publication**: execute `python -m pip install -e ".[dev]"`, `python -m compileall -q optimizer tests`, `python -m pytest -q` and documented CLI smoke tests. Check CI job logs and packaging, then publish only a verified deliverable.

## Agent operating prompt

Implement one concrete functional improvement with regression test per iteration. Verify the available environment before claiming success. Commit focused changes, preserve the project canon, and do not create additional repositories. If CI jobs fail before any runner is assigned, report infrastructure verification as blocked, not as a failed code test and not as a passing test.

## Changes recorded — 2026-10-23

- `optimizer/recommender.py`: in-budget jobs retain their original quality settings; very narrow resolutions are never increased while searching for lower-cost scenarios.
- `tests/test_recommender.py`: regression cases for both behaviors.
- **Validation status**: GitHub Actions reported failure before assigning a runner (`runner_id=0`, no steps); code execution remains unverified until an available runner or an authorized local environment can execute the suite.
