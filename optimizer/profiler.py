"""Workflow profiling for diffusion pipelines.

In production, profile_workflow would execute the actual pipeline and time each
step. This module provides the public API plus simulated profiling for offline
analysis and testing.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from optimizer.pricing import GPU_PRICES, calculate_cost


@dataclass
class StepTiming:
    """Timing for a single pipeline step."""
    step_name: str
    elapsed_seconds: float
    vram_peak_mb: float = 0.0


@dataclass
class ProfileResult:
    """Full profiling result for a workflow execution."""
    workflow_name: str
    gpu: str
    steps: list[StepTiming] = field(default_factory=list)
    total_seconds: float = 0.0
    vram_limit_gb: float = 0.0

    @property
    def step_times(self) -> list[float]:
        return [s.elapsed_seconds for s in self.steps]


def validate_workflow(workflow: dict[str, Any]) -> None:
    """Reject malformed inputs before estimating time, VRAM or cost."""
    if not isinstance(workflow, dict):
        raise ValueError("Workflow must be a JSON object")
    resolution = workflow.get("resolution", [512, 512])
    if (not isinstance(resolution, (list, tuple)) or len(resolution) != 2
            or any(type(n) is not int or n < 1 or n > 16384 for n in resolution)):
        raise ValueError("resolution must contain two integers between 1 and 16384")
    scheduler = workflow.get("scheduler", {})
    if not isinstance(scheduler, dict):
        raise ValueError("scheduler must be a JSON object")
    steps = scheduler.get("steps", 30)
    if type(steps) is not int or not 1 <= steps <= 1000:
        raise ValueError("scheduler.steps must be an integer between 1 and 1000")
    batch = workflow.get("batch_size", 1)
    if type(batch) is not int or not 1 <= batch <= 4096:
        raise ValueError("batch_size must be an integer between 1 and 4096")


def measure_step_times(workflow: dict[str, Any]) -> list[float]:
    """Estimate per-step execution times for a workflow.

    Returns realistic time estimates based on resolution, steps, and batch
    size. In a real implementation this would run the actual pipeline.
    """
    res_w, res_h = workflow.get("resolution", [512, 512])
    sched = workflow.get("scheduler", {})
    num_steps = sched.get("steps", 30)
    batch = workflow.get("batch_size", 1)
    megapixels = (res_w * res_h) / 1_000_000

    # Base times in seconds for an A100-class GPU at 1024x1024, 30 steps, bs=1
    base = {
        "vae_encode": 0.12 * megapixels,
        "text_encode": 0.08,
        "denoise": 1.8 * megapixels * (num_steps / 30.0),
        "vae_decode": 0.15 * megapixels,
        "safety_check": 0.05 if workflow.get("safety_checker", False) else 0.0,
    }
    times: list[float] = []
    for name, t in base.items():
        adjusted = t * batch
        times.append(round(adjusted, 4))
    return times


def estimate_total_cost(profile: ProfileResult, gpu_pricing: dict[str, float]) -> float:
    """Estimate total cost from a profile result.

    Args:
        profile: Completed ProfileResult.
        gpu_pricing: Map of gpu name -> $/hour (overrides profile.gpu lookup).

    Returns:
        Estimated cost in USD.
    """
    if (isinstance(profile.total_seconds, bool)
            or not isinstance(profile.total_seconds, (int, float))
            or not math.isfinite(profile.total_seconds)
            or profile.total_seconds < 0):
        raise ValueError("Profile runtime must be finite and non-negative")

    if not isinstance(profile.gpu, str) or not profile.gpu.strip():
        raise ValueError("GPU name must be a non-empty string")
    if not isinstance(gpu_pricing, dict):
        raise ValueError("GPU pricing overrides must be a mapping")
    gpu = profile.gpu.lower().replace("-", "").replace(" ", "")
    overrides = {}
    for sku, hourly_price in gpu_pricing.items():
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("GPU pricing override names must be non-empty strings")
        normalized_sku = sku.lower().replace("-", "").replace(" ", "")
        if normalized_sku in overrides:
            raise ValueError(f"Duplicate GPU pricing override for {normalized_sku}")
        overrides[normalized_sku] = hourly_price

    if gpu in overrides:
        price = overrides[gpu]
    else:
        info = GPU_PRICES.get(gpu)
        if info is None:
            raise ValueError(f"Unknown GPU price: {profile.gpu}. Supply a valid override.")
        price = info["price_per_hour"]

    if (isinstance(price, bool) or not isinstance(price, (int, float))
            or not math.isfinite(price) or price < 0):
        raise ValueError("GPU hourly price must be finite and non-negative")
    return (profile.total_seconds / 3600.0) * price


def profile_workflow(workflow: dict[str, Any], gpu: str = "a100") -> ProfileResult:
    """Profile a diffusion workflow on a given GPU.

    Runs simulated timing and produces a ProfileResult with per-step
    breakdown and total cost estimate.

    Args:
        workflow: Workflow definition dict.
        gpu: GPU identifier.

    Returns:
        ProfileResult with timing data.
    """
    validate_workflow(workflow)
    gpu_lower = gpu.lower().replace("-", "").replace(" ", "")
    if gpu_lower not in GPU_PRICES:
        raise ValueError(f"Unknown GPU: {gpu}. Available: {', '.join(sorted(GPU_PRICES))}")
    gpu_info = GPU_PRICES[gpu_lower]
    gpu_tflops = gpu_info.get("fp16_tflops", 200.0)
    a100_tflops = 312.0  # reference

    step_times = measure_step_times(workflow)
    step_names = ["vae_encode", "text_encode", "denoise", "vae_decode", "safety_check"]
    timings: list[StepTiming] = []

    for name, t in zip(step_names, step_times):
        # Scale by GPU relative performance
        scaled = t * (a100_tflops / gpu_tflops) if gpu_tflops > 0 else t
        timings.append(StepTiming(step_name=name, elapsed_seconds=round(scaled, 4)))

    total = sum(t.elapsed_seconds for t in timings)

    res_w, res_h = workflow.get("resolution", [512, 512])
    megapixels = (res_w * res_h) / 1_000_000
    vram_est = 4.0 + megapixels * 2.0 + workflow.get("batch_size", 1) * 1.5

    return ProfileResult(
        workflow_name=workflow.get("name", "unnamed"),
        gpu=gpu,
        steps=timings,
        total_seconds=round(total, 4),
        vram_limit_gb=round(vram_est, 2),
    )


def load_workflow(path: str | Path) -> dict[str, Any]:
    """Load a workflow JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Workflow file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        result = json.load(f)
    validate_workflow(result)
    return result
