# Design — Offline calculator and dependable CLI

## Decision

Use the existing Python package as the canonical heuristic model and implement the browser surface as a static, dependency-free calculator. Preserve existing package architecture, CLI entry points, sample workflow, and GitHub Pages deployment. The frontend mirrors only public model inputs, supported GPU data, and calculation formulas; parity fixtures and documented assumptions guard drift.

## Browser structure

- Semantic form for workflow inputs with import and sample loading.
- Result panel for runtime stages, VRAM, cost and GPU comparison.
- A visible methodology/provenance section stating that the values are simulations and the bundled tariffs are historical references.
- Separate workflow and result downloads, generated locally in the browser.
- Optional local browser state for draft workflow continuity, enabled only when the user opts in; no account or telemetry.

## Python/CLI structure

- Keep workflow validation in the profiling layer and convert file/decode/validation failures to concise Click errors.
- Serialize report data through a dedicated JSON-safe representation, excluding internal applied-workflow objects unless explicitly needed.
- Preserve Markdown report as the default format and add explicit JSON selection.
- Add model provenance constants for formula/version and historical tariff reference in exported reports.

## Accessibility and visual system

Use repository tokens: #05030a, #ff073a, #d4af37, and #4de8e0. Maintain body contrast of at least 4.5:1, 65–75ch reading measure, visible focus, 44px touch targets, semantic headings/labels, reduced-motion support, and non-card-based editorial result layout. Avoid gradient text, repeated eyebrow labels, nested cards, and arbitrary z-index values.

## Validation

Use GWT acceptance cases for browser form, import/export, feasibility, and error states; pytest coverage for Python validation/serialization/CLI; static checks for HTML/JS and browser/Python fixture parity. Run the exact repository install, compile, tests, and CLI smoke commands before delivery.
