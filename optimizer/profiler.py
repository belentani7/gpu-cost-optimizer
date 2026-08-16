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
    gpu = profile.gpu.lower().replace("-", "")
    price = gpu_pricing.get(gpu)
    if price is None:
        info = GPU_PRICES.get(gpu, {})
        price = info.get("price_per_hour", 0.0)
    if price == 0.0:
        return 0.0
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
    gpu_lower = gpu.lower().replace("-", "")
    gpu_info = GPU_PRICES.get(gpu_lower, {"price_per_hour": 1.0})
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
        return json.load(f)
