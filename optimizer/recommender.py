"""Smart GPU and settings recommendations based on workflow requirements."""

from __future__ import annotations

from dataclasses import dataclass
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
    comparisons = compare_gpus(workflow)
    affordable = [c for c in comparisons if c.estimated_cost <= budget]
    if affordable:
        # Best score (lowest cost-weighted time)
        return min(affordable, key=lambda c: c.score).gpu
    # If nothing fits, return the cheapest option
    return min(comparisons, key=lambda c: c.estimated_cost).gpu


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
    gpu = workflow.get("target_gpu", "a100")
    vram = GPU_PRICES.get(gpu.lower().replace("-", ""), {}).get("vram_gb", 24.0)

    wf = workflow.copy()
    for _ in range(10):
        optimized = apply_all_strategies(wf, vram_limit=vram)
        profile = profile_workflow(optimized, gpu=gpu)
        cost = calculate_cost(gpu, profile.total_seconds)
        if cost <= target_cost:
            return optimized
        # If still too expensive, reduce resolution further
        res = optimized.get("resolution", [512, 512])
        if res[0] > 256:
            optimized["resolution"] = [max(256, res[0] // 2), max(256, res[1] // 2)]
            wf = optimized
        else:
            break

    return apply_all_strategies(wf, vram_limit=vram)


def compare_gpus(workflow: dict[str, Any]) -> list[GPUComparison]:
    """Compare all available GPUs for a given workflow.

    Args:
        workflow: Workflow definition.

    Returns:
        List of GPUComparison sorted by score (best first).
    """
    results: list[GPUComparison] = []
    res = workflow.get("resolution", [512, 512])
    megapixels = (res[0] * res[1]) / 1_000_000
    batch = workflow.get("batch_size", 1)
    steps = workflow.get("scheduler", {}).get("steps", 30)

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
