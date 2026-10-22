"""Explicit-rate GPU invoice scenario planner.

The GPU timings and estimated VRAM come from the existing *heuristic* profiler.
The price is ALWAYS supplied by the operator: bundled GPU prices are historical
reference only and must not be silently treated as October 2026 quotations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

from optimizer.pricing import get_gpu_info
from optimizer.profiler import profile_workflow


def _amount(value: float | int, label: str, *, minimum: float = 0,
            maximum: float = 1_000_000_000) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{label} must be finite, between {minimum} and {maximum}")
    return number


@dataclass(frozen=True)
class BillingScenario:
    workflow: str
    gpu: str
    currency: str
    source: str
    user_supplied_rate_usd_hour: float
    jobs: int
    estimated_compute_seconds_each: float
    startup_seconds_each: float
    minimum_billable_seconds_each: float
    billing_quantum_seconds: int
    billed_seconds_each: float
    total_billed_hours: float
    quoted_gpu_compute_usd: float
    quoted_gpu_bill_usd: float
    startup_and_rounding_overhead_usd: float
    estimated_vram_gb: float
    available_vram_gb: float
    fits_vram_heuristic: bool
    conditions: tuple[str, ...]

    def json(self) -> dict[str, Any]:
        result = asdict(self)
        result["conditions"] = list(self.conditions)
        return result


def quote_workflow(
    workflow: dict[str, Any], *, gpu: str, rate_usd_hour: float, jobs: int = 1,
    startup_seconds: float = 0.0, minimum_billable_seconds: float = 0.0,
    billing_quantum_seconds: int = 1,
) -> BillingScenario:
    """Compare bare GPU compute with per-job billable duration.

    Bills each job individually; jobs sharing a warm server or sustained
    reservations should be represented by a different provider invoice model.
    """
    hourly = _amount(rate_usd_hour, "rate_usd_hour", maximum=1_000_000)
    if hourly <= 0:
        raise ValueError("rate_usd_hour must be greater than zero; no bundled price is assumed")
    if type(jobs) is not int or not 1 <= jobs <= 1_000_000:
        raise ValueError("jobs must be an integer between 1 and 1000000")
    startup = _amount(startup_seconds, "startup_seconds", maximum=86_400)
    minimum = _amount(minimum_billable_seconds, "minimum_billable_seconds", maximum=86_400)
    if type(billing_quantum_seconds) is not int or not 1 <= billing_quantum_seconds <= 3600:
        raise ValueError("billing_quantum_seconds must be between 1 and 3600")
    spec = get_gpu_info(gpu)
    estimated = profile_workflow(workflow, gpu)
    runtime = estimated.total_seconds
    billed_each = (
        math.ceil(max(runtime + startup, minimum) / billing_quantum_seconds)
        * billing_quantum_seconds
    )
    billed_hours = billed_each * jobs / 3600
    bare_gpu_usd = (runtime * jobs / 3600) * hourly
    billed_usd = billed_hours * hourly
    fits = estimated.vram_limit_gb <= float(spec["vram_gb"])
    notes = (
        "GPU duration and VRAM are heuristic projections, not device measurements.",
        "Hourly rate is operator supplied. Confirm current vendor pricing and billing minimums.",
        "Assumes every job incurs its own startup time and independent billing round-up.",
        "Excludes taxes, storage, data egress, API charges, queue time and contractual discounts.",
        "A VRAM fit flag is a heuristic, not proof that this model actually runs on the GPU.",
    )
    if not fits:
        notes += ("WARNING: projected VRAM exceeds selected GPU capacity; do not purchase without a compatibility test.",)
    return BillingScenario(
        workflow=str(workflow.get("name", "unnamed"))[:120],
        gpu=gpu.lower().replace("-", "").replace(" ", ""),
        currency="USD",
        source="explicit-user-rate + offline-heuristic-profile",
        user_supplied_rate_usd_hour=hourly,
        jobs=jobs,
        estimated_compute_seconds_each=round(runtime, 4),
        startup_seconds_each=startup,
        minimum_billable_seconds_each=minimum,
        billing_quantum_seconds=billing_quantum_seconds,
        billed_seconds_each=billed_each,
        total_billed_hours=round(billed_hours, 8),
        quoted_gpu_compute_usd=round(bare_gpu_usd, 6),
        quoted_gpu_bill_usd=round(billed_usd, 6),
        startup_and_rounding_overhead_usd=round(billed_usd - bare_gpu_usd, 6),
        estimated_vram_gb=estimated.vram_limit_gb,
        available_vram_gb=float(spec["vram_gb"]),
        fits_vram_heuristic=fits,
        conditions=notes,
    )
