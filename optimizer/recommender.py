"""Smart GPU and settings recommendations based on workflow requirements."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from optimizer.pricing import GPU_PRICES, calculate_cost
from optimizer.profiler import profile_workflow
from optimizer.strategies import apply_all_strategies


@dataclass
class GPUComparison:
    """Comparison of a GPU for a given workflow."""
    gpu: str
    price_per_hour: float
    vram_gb: float
    estimated_time_seconds: float
    estimated_cost: float
    meets_vram: bool
    score: float  # lower is better (cost-weighted)


def recommend_gpu(workflow: dict[str, Any], budget: float) -> str:
    """Recommend the best GPU for a workflow within a budget.

    Args:
        workflow: Workflow definition.
        budget: Maximum cost per run in USD.

    Returns:
        GPU identifier string.
    """
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be a finite, positive USD amount")

    comparisons = compare_gpus(workflow)
    feasible = [c for c in comparisons if c.meets_vram]
    if not feasible:
        required = max(c.vram_gb for c in comparisons)
        raise ValueError(
            "No listed GPU has enough estimated VRAM for this workflow. "
            f"Available VRAM is at most {required:g} GB; reduce batch or resolution."
        )
    affordable = [c for c in feasible if c.estimated_cost <= budget]
    if not affordable:
        minimum = min(c.estimated_cost for c in feasible)
        raise ValueError(
            "No VRAM-compatible GPU meets the per-run budget of "
            f"${budget:.6f}; estimated minimum is ${minimum:.6f}. "
            "Raise the budget or reduce workload complexity."
        )
    # A feasible, affordable option always wins over a nominally cheap GPU
    # whose estimated VRAM requirement cannot be satisfied.
    return min(affordable, key=lambda c: (c.estimated_cost, c.estimated_time_seconds)).gpu


def recommend_settings(
    workflow: dict[str, Any],
    target_cost: float,
) -> dict[str, Any]:
    """Recommend workflow settings to hit a target cost.

    Iteratively applies optimizations until cost is at or below target.

    Args:
        workflow: Workflow definition.
        target_cost: Target cost per run in USD.

    Returns:
        Optimized workflow dict.
    """
    if not math.isfinite(target_cost) or target_cost <= 0:
        raise ValueError("target_cost must be a finite amount greater than zero")

    gpu = workflow.get("target_gpu", "a100")
    # Preserve quality and the author's explicit settings when already in budget.
    baseline = profile_workflow(workflow, gpu=gpu)
    if calculate_cost(gpu, baseline.total_seconds) <= target_cost:
        return workflow.copy()

    vram = GPU_PRICES.get(gpu.lower().replace("-", ""), {}).get("vram_gb", 24.0)

    wf = workflow.copy()
    for _ in range(10):
        optimized = apply_all_strategies(wf, vram_limit=vram)
        profile = profile_workflow(optimized, gpu=gpu)
        cost = calculate_cost(gpu, profile.total_seconds)
        if cost <= target_cost:
            return optimized
        # Further reductions must never INCREASE either dimension.
        # A narrow portrait image (512x128) previously jumped to 256x256.
        res = optimized.get("resolution", [512, 512])
        reduced = [
            max(256, dimension // 2) if dimension > 256 else dimension
            for dimension in res
        ]
        if reduced == list(res):
            break
        optimized["resolution"] = reduced
        wf = optimized

    return apply_all_strategies(wf, vram_limit=vram)


def compare_gpus(workflow: dict[str, Any]) -> list[GPUComparison]:
    """Compare all available GPUs for a given workflow.

    Args:
        workflow: Workflow definition.

    Returns:
        List of GPUComparison sorted by score (best first).
    """
    results: list[GPUComparison] = []

    for gpu_id, info in GPU_PRICES.items():
        profile = profile_workflow(workflow, gpu=gpu_id)
        cost = calculate_cost(gpu_id, profile.total_seconds)
        meets = profile.vram_limit_gb <= info["vram_gb"]

        # Score: cost per unit of compute
        score = cost if meets else cost * 10  # penalize VRAM-insufficient

        results.append(
            GPUComparison(
                gpu=gpu_id,
                price_per_hour=info["price_per_hour"],
                vram_gb=info["vram_gb"],
                estimated_time_seconds=profile.total_seconds,
                estimated_cost=round(cost, 6),
                meets_vram=meets,
                score=round(score, 6),
            )
        )

    return sorted(results, key=lambda c: c.score)
