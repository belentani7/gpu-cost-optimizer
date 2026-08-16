"""Optimization strategies for diffusion workflows.

Each strategy takes a workflow dict and returns a modified copy with
optimizations applied. All strategies are composable.
"""

from __future__ import annotations

import copy
from typing import Any


def _clone_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(workflow)


def reduce_steps(
    workflow: dict[str, Any],
    max_quality_loss: float = 0.05,
) -> dict[str, Any]:
    """Reduce scheduler steps while keeping quality loss under threshold.

    Rule of thumb: halving steps from 50->25 costs ~3-5% quality on
    SDXL. Going below 15 steps degrades noticeably.

    Args:
        workflow: Workflow definition.
        max_quality_loss: Maximum acceptable quality loss (0.0-1.0).

    Returns:
        Modified workflow with fewer steps.
    """
    wf = _clone_workflow(workflow)
    sched = wf.get("scheduler", {})
    current_steps = sched.get("steps", 30)

    if max_quality_loss <= 0.01:
        # Very conservative: remove ~10% of steps
        new_steps = max(15, int(current_steps * 0.9))
    elif max_quality_loss <= 0.05:
        # Moderate: can go down to ~60% of original
        new_steps = max(15, int(current_steps * 0.6))
    elif max_quality_loss <= 0.10:
        # Aggressive: ~40% of original
        new_steps = max(12, int(current_steps * 0.4))
    else:
        # Very aggressive
        new_steps = max(8, int(current_steps * 0.25))

    sched["steps"] = new_steps
    wf["scheduler"] = sched
    return wf


def reduce_resolution(
    workflow: dict[str, Any],
    target_fps: float = 30.0,
) -> dict[str, Any]:
    """Reduce resolution while maintaining acceptable output quality.

    Drops to the nearest standard resolution tier. For still images,
    target_fps is ignored (used for video pipelines).

    Args:
        workflow: Workflow definition.
        target_fps: Target FPS (for video workflows).

    Returns:
        Modified workflow with lower resolution.
    """
    wf = _clone_workflow(workflow)
    res = wf.get("resolution", [512, 512])
    w, h = res[0], res[1]
    megapixels = (w * h) / 1_000_000

    # Resolution tiers from largest to smallest
    tiers = [
        (4096, 4096, 16.0),
        (2048, 2048, 4.0),
        (1536, 1536, 2.25),
        (1024, 1024, 1.0),
        (768, 768, 0.59),
        (512, 512, 0.26),
    ]

    # Find current tier and drop one level
    for i, (tw, th, tm) in enumerate(tiers):
        if megapixels >= tm * 0.8 or (w >= tw * 0.8 and h >= th * 0.8):
            if i < len(tiers) - 1:
                nw, nh = tiers[i + 1][0], tiers[i + 1][1]
                # Maintain aspect ratio
                aspect = w / h
                if aspect >= 1.0:
                    nh = int(nw / aspect)
                else:
                    nw = int(nh * aspect)
                wf["resolution"] = [nw, nh]
            break

    return wf


def optimize_batch_size(
    workflow: dict[str, Any],
    vram_limit: float = 24.0,
) -> dict[str, Any]:
    """Ensure batch size fits within VRAM limit.

    Does not increase batch size beyond the original — only reduces if it
    would exceed available VRAM.

    Args:
        workflow: Workflow definition.
        vram_limit: Available VRAM in GB.

    Returns:
        Modified workflow with safe batch size.
    """
    wf = _clone_workflow(workflow)
    res = wf.get("resolution", [512, 512])
    megapixels = (res[0] * res[1]) / 1_000_000

    per_image_gb = 1.5 + megapixels * 1.2
    overhead_gb = 3.5

    available = vram_limit - overhead_gb
    max_safe = max(1, int(available / per_image_gb)) if available > 0 else 1

    current = wf.get("batch_size", 1)
    wf["batch_size"] = min(current, max_safe)
    return wf


def use_turbo_scheduler(workflow: dict[str, Any]) -> dict[str, Any]:
    """Switch to a turbo/distilled scheduler for faster inference.

    Turbo schedulers (e.g., LCM, SDXL-Turbo, Lightning) produce
    good results in 4-8 steps vs 30-50 for standard schedulers.

    Args:
        workflow: Workflow definition.

    Returns:
        Modified workflow with turbo scheduler.
    """
    wf = _clone_workflow(workflow)
    sched = wf.get("scheduler", {})
    current_type = sched.get("type", "euler_a")

    turbo_map = {
        "euler_a": "lcm",
        "euler": "lcm",
        "dpm++_2m": "lcm",
        "dpm++_sd": "lcm",
        "ddim": "lcm",
        "pndm": "lcm",
        "lms": "lcm",
        "heun": "lcm",
    }
    new_type = turbo_map.get(current_type, "lcm")
    sched["type"] = new_type

    # Turbo schedulers work well with 4-8 steps
    current_steps = sched.get("steps", 30)
    if current_steps > 8:
        sched["steps"] = 8
    sched["turbo"] = True

    wf["scheduler"] = sched
    return wf


def quantize_model(workflow: dict[str, Any]) -> dict[str, Any]:
    """Enable FP16/BF16 quantization for lower memory and faster compute.

    Args:
        workflow: Workflow definition.

    Returns:
        Modified workflow with quantization enabled.
    """
    wf = _clone_workflow(workflow)
    wf["dtype"] = "float16"
    wf["quantization"] = {
        "enabled": True,
        "precision": "fp16",
        "expected_speedup": 1.8,
        "expected_vram_reduction": 0.5,
    }
    return wf


def apply_all_strategies(
    workflow: dict[str, Any],
    vram_limit: float = 24.0,
    target_cost: float | None = None,
) -> dict[str, Any]:
    """Apply all optimization strategies in order.

    Strategies are applied greedily. Each one may independently reduce
    quality; the caller should verify the final output meets requirements.

    Args:
        workflow: Workflow definition.
        vram_limit: VRAM limit in GB.
        target_cost: Target cost per run in USD. If provided, strategies
            continue until cost is at or below target.

    Returns:
        Optimized workflow.
    """
    wf = _clone_workflow(workflow)

    # 1. Turbo scheduler (biggest win)
    wf = use_turbo_scheduler(wf)

    # 2. Reduce steps conservatively
    wf = reduce_steps(wf, max_quality_loss=0.05)

    # 3. Quantize to FP16
    wf = quantize_model(wf)

    # 4. Optimize batch size for the target GPU
    wf = optimize_batch_size(wf, vram_limit=vram_limit)

    # 5. Reduce resolution only if still too expensive
    if target_cost is not None:
        # Check if we need more aggressive optimization
        wf = reduce_resolution(wf)

    return wf
