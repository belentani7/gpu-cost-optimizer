# SRS — GPU Cost Optimizer

## Functional requirements

### FR-1 Workflow entry
The browser app shall provide labeled controls for workflow name, pipeline/model, scheduler and step count, width/height, batch size, safety checker, and target GPU. It shall import a workflow JSON file and validate it before estimation.

### FR-2 Estimates
The app shall calculate simulated stage durations, estimated VRAM, and per-run estimated cost using the same documented heuristics and historical tariff values as the Python package. It shall compare all supported GPUs, identify VRAM-incompatible choices, and label cost and performance results as estimates.

### FR-3 Results and exports
The app shall show the assumptions and historical tariff date/status beside results. It shall export the edited workflow JSON and a result JSON that includes inputs, estimates, model/version metadata, and an explicit simulation disclaimer.

### FR-4 CLI
Existing commands remain available. Invalid workflow JSON and invalid workflow data shall produce concise actionable errors. The report command shall support machine-readable JSON output without breaking Markdown output.

### FR-5 Accessibility and resilience
The app shall support keyboard use, visible focus, responsive layout, reduced motion, readable contrast, and designed empty/error states. Core calculations shall work offline in a modern browser without third-party scripts.

### FR-6 Commercial transparency
The public page shall list the free Base offer and the proposed rates for optional Support (€89/month), Managed (€149/month), and Consulting (€89/hour). It shall say that these are proposed rates, core features remain free, and service scope/availability are agreed separately. It shall not collect payments or gate product features.

## Non-functional requirements

- Python 3.9+ compatibility and no new runtime service dependency.
- Deterministic calculation for identical inputs and tariff data.
- Validate bounded numeric inputs before calculations; never execute imported content.
- Preserve imported workflow fields not edited by the UI when exporting.
- Persist drafts only after explicit opt-in; allow clearing the saved draft.
- Tests cover valid workflows, malformed inputs, numeric boundaries, exports, and browser/Python parity on fixtures.

## Acceptance criteria

1. A user can load the included sample, change parameters, calculate results, and compare GPUs with no network connection.
2. Invalid or infeasible cases show an understandable message and do not display a misleading recommendation.
3. Exported workflow JSON passes the Python loader; exported result JSON carries assumptions and tariff provenance.
4. CLI Markdown and JSON reports are valid and deterministic for the same workflow.
5. Existing CLI commands and regression suite continue to work.
