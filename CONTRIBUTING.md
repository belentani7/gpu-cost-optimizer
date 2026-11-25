# Contributing to GPU Cost Optimizer

Thanks for your interest in improving this project. This guide explains how to
set up your environment, what the quality gates are, and how to submit changes.

## Ground rules

- Model estimates are **heuristics, not benchmarks**. Never describe simulated
  times, VRAM figures, or historical reference prices as live measurements,
  quotes, or guarantees. Keep the transparency notices intact.
- The offline contract matters: the tool must keep working without a GPU, an
  account, credentials, or network access.
- Zero regression: if a change breaks an existing behavior, revert it.

## Development setup

```bash
git clone https://github.com/belentani7/gpu-cost-optimizer.git
cd gpu-cost-optimizer
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Quality gates

Run these before opening a pull request. All of them must pass:

```bash
python -m compileall -q optimizer tests
python -m pytest -q
node --test tests/web-*.test.cjs
python scripts/doctor.py
gpuopt --help
gpuopt profile examples/workflow.json --gpu a100
```

Pull requests that only pass partially will not be merged. CI runs the same
matrix (Python 3.9 and 3.12) plus the web publication contract.

## Project conventions

- **Spec-first protocol**: PRD → SRS → Design Doc → ADR → Plan → GWT tests.
  See `docs/specs/` for a worked example.
- **Tokens and brand**: follow `brand/tokens.css` and the AGENTS.md checklist
  for frontend changes (contrast ≥ 4.5:1, touch targets ≥ 44px,
  `prefers-reduced-motion` respected, no nested cards).
- **Commits**: `type(scope): summary` with one of `feat`, `fix`, `docs`,
  `chore`, `refactor`, `test`, `perf`, `style`.
- **Dependencies**: the runtime depends only on `click` and `rich`. Adding a
  new runtime dependency requires a justification in the PR description.

## Reporting issues

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Include:

- version or commit SHA,
- steps to reproduce,
- expected vs. actual output,
- whether the issue is in the CLI, the web calculator, or the docs.

## Security vulnerabilities

Do **not** open a public issue. Follow [SECURITY.md](SECURITY.md).

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
