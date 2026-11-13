# Acceptance cases — Given / When / Then

## GWT-1: estimate a valid workflow

Given the sample diffusion workflow is loaded, when the user calculates with A100 selected, then the app displays simulated per-stage time, estimated VRAM, and estimated USD cost with the assumptions visible.

## GWT-2: compare GPU feasibility

Given a valid workflow, when the user requests comparison, then every supported GPU is shown with estimated price, duration, VRAM, and a feasibility label; an incompatible GPU is never called recommended.

## GWT-3: import valid JSON

Given a valid workflow JSON file, when the user imports it, then its supported fields populate the form and calculation can run without a network request.

## GWT-4: reject malformed input

Given malformed JSON or out-of-range numeric fields, when the user imports or calculates, then the app presents an actionable error and keeps the last valid result clearly separate from the failed attempt.

## GWT-5: export reproducible data

Given a completed estimate, when the user exports workflow and result JSON, then workflow JSON can be loaded by `gpuopt`, and result JSON includes model version, inputs, historical tariff provenance, estimates, and the simulation disclaimer.

## GWT-6: CLI report formats

Given a valid workflow file, when `gpuopt report` is run in Markdown mode or JSON mode, then the selected output is valid, deterministic, and contains the same underlying estimate data.

## GWT-7: optional service offer

Given the public product page is opened, when the visitor reviews service options, then it lists the free Base offer and proposed Support, Managed, and Consulting rates, states that the core remains free with no in-app checkout, and links to the maintainer profile for enquiries.
