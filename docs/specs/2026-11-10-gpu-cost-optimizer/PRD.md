# PRD — GPU Cost Optimizer

## Intent

Help diffusion workflow authors compare plausible runtime, historical GPU cost, and estimated VRAM before renting compute. The product is an offline decision aid; it does not run models, measure hardware, promise savings, or fetch current provider tariffs.

## Users and success

The primary users are independent creators and engineering teams who need to understand the cost implications of a diffusion workflow before running it. A user succeeds when they can inspect a clearly qualified estimate, compare compatible GPUs, and export the inputs and result for review.

## Goals

- Make the existing Python package usable through a reliable CLI and an accessible static browser calculator.
- Keep the browser experience usable without an account, server, network request, or GPU.
- Make assumptions, historical tariff provenance, and feasibility limits visible next to estimates.
- Support workflow JSON import/export and a reproducible result export.
- Preserve user input and the existing Python package API where practical.

## Non-goals

- Executing, benchmarking, or validating diffusion models and schedulers.
- Live provider price discovery, cloud account integrations, billing, or hosted user data.
- Guarantees about image quality, throughput, VRAM use, or savings.

## Constraints

Retain Python 3.9+ and the existing `gpuopt` package/CLI. The web app remains static and dependency-free. Historical prices must never be represented as current quotes. Follow the repository design canon and accessibility checklist.

## Approaches

1. CLI-only hardening: lowest implementation risk, but leaves the current generic web page without product utility.
2. Static offline calculator plus consistent CLI improvements: chosen because it makes the product approachable while preserving its offline architecture and existing package.
3. Hosted service with live prices: rejected because it changes the defined product boundary and introduces network, account, and data dependencies.

## Product direction

Deliver approach 2. The browser calculator accepts the documented workflow fields, estimates stage timing/cost/VRAM across listed GPUs, highlights assumptions and feasibility, and exports workflow/result JSON. The CLI retains its established commands and gains consistent, safe machine-readable report output and input errors where needed. No service or live pricing is added.

## Risks

The web calculator necessarily mirrors the documented heuristic model. Keep formulas and model provenance visible, and add regression coverage that compares web and Python outputs for canonical fixtures. Historical prices and simulated performance remain unsuitable for purchase decisions without provider and benchmark verification.
