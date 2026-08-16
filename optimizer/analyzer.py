"""Cost analysis and bottleneck detection for diffusion workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from optimizer.pricing import GPU_PRICES, calculate_cost
from optimizer.profiler import ProfileResult, profile_workflow
from optimizer.strategies import apply_all_strategies


@dataclass
class Bottleneck:
    """Identified performance bottleneck."""
    step: str
    seconds: float
    percentage: float
    description: str


@dataclass
class Optimization:
    """A suggested optimization."""
    name: str
    description: str
    estimated_savings_pct: float
    estimated_savings_usd: float
    quality_impact: str
    applied_workflow: dict = field(repr=False)


@dataclass
class CostReport:
    """Full cost analysis report for a workflow."""
    workflow_name: str
    gpu: str
    original_cost: float
    optimized_cost: float
    savings_usd: float
    savings_pct: float
    bottlenecks: list[Bottleneck]
    optimizations: list[Optimization]
    original_profile: ProfileResult | None = None
    optimized_profile: ProfileResult | None = None


def find_bottlenecks(profile: ProfileResult) -> list[Bottleneck]:
    """Identify the most time-consuming steps in a profile.

    A step is considered a bottleneck if it accounts for more than 30%
    of total execution time.
    """
    total = profile.total_seconds
    if total <= 0:
        return []

    bottlenecks: list[Bottleneck] = []
    descriptions = {
        "denoise": "Denoising loop is the primary compute bottleneck. "
                   "Reducing steps or switching to a turbo scheduler helps most.",
        "vae_encode": "VAE encoding overhead. Consider using tiled VAE or "
                      "lower resolution input.",
        "vae_decode": "VAE decoding overhead. Tiled VAE decoding reduces "
                      "memory and time.",
        "text_encode": "Text encoding is typically fast but scales with "
                       "prompt length.",
        "safety_check": "Safety checker adds fixed overhead. Disable if not "
                        "required.",
    }

    for step in profile.steps:
        pct = (step.elapsed_seconds / total) * 100 if total > 0 else 0
        if pct >= 30.0 or step.step_name == "denoise":
            bottlenecks.append(
                Bottleneck(
                    step=step.step_name,
                    seconds=step.elapsed_seconds,
                    percentage=round(pct, 1),
                    description=descriptions.get(step.step_name, "Significant step."),
                )
            )

    return sorted(bottlenecks, key=lambda b: b.seconds, reverse=True)


def suggest_optimizations(profile: ProfileResult) -> list[Optimization]:
    """Suggest optimizations based on profiling data.

    Returns a list of Optimization objects with estimated savings.
    """
    optimizations: list[Optimization] = []
    gpu_info = GPU_PRICES.get(profile.gpu.lower().replace("-", ""), {})
    price_per_hour = gpu_info.get("price_per_hour", 1.0)
    price_per_sec = price_per_hour / 3600.0

    # Turbo scheduler suggestion
    denoise = next((s for s in profile.steps if s.step_name == "denoise"), None)
    if denoise and denoise.elapsed_seconds > 1.0:
        turbo_savings = denoise.elapsed_seconds * 0.7  # ~70% reduction in denoise time
        turbo_cost = turbo_savings * price_per_sec
        optimizations.append(
            Optimization(
                name="Turbo Scheduler (LCM)",
                description="Switch to LCM turbo scheduler (8 steps instead of 30+)",
                estimated_savings_pct=round((turbo_savings / profile.total_seconds) * 100, 1),
                estimated_savings_usd=round(turbo_cost, 6),
                quality_impact="Minor - 3-5% quality loss on standard benchmarks",
                applied_workflow={},
            )
        )

    # Step reduction
    if denoise and denoise.elapsed_seconds > 0.5:
        step_savings = denoise.elapsed_seconds * 0.4  # ~40% reduction
        step_cost = step_savings * price_per_sec
        optimizations.append(
            Optimization(
                name="Reduce Steps",
                description="Reduce scheduler steps from 50 to 20",
                estimated_savings_pct=round((step_savings / profile.total_seconds) * 100, 1),
                estimated_savings_usd=round(step_cost, 6),
                quality_impact="Low - 3% quality loss",
                applied_workflow={},
            )
        )

    # Resolution reduction
    if profile.vram_limit_gb > 8.0:
        res_savings = profile.total_seconds * 0.25
        res_cost = res_savings * price_per_sec
        optimizations.append(
            Optimization(
                name="Reduce Resolution",
                description="Drop one resolution tier (e.g., 1024x1024 -> 768x768)",
                estimated_savings_pct=round((res_savings / profile.total_seconds) * 100, 1),
                estimated_savings_usd=round(res_cost, 6),
                quality_impact="Moderate - visible quality reduction for prints",
                applied_workflow={},
            )
        )

    # FP16 quantization
    quant_savings = profile.total_seconds * 0.15
    quant_cost = quant_savings * price_per_sec
    optimizations.append(
        Optimization(
            name="FP16 Quantization",
            description="Run model in FP16 precision (2x less VRAM, ~1.8x faster)",
            estimated_savings_pct=round((quant_savings / profile.total_seconds) * 100, 1),
            estimated_savings_usd=round(quant_cost, 6),
            quality_impact="Negligible - standard practice for inference",
            applied_workflow={},
        )
    )

    return sorted(optimizations, key=lambda o: o.estimated_savings_pct, reverse=True)


def analyze_workflow(workflow: dict[str, Any], gpu: str = "a100") -> CostReport:
    """Perform full cost analysis on a workflow.

    Profiles the workflow, identifies bottlenecks, suggests optimizations,
    and computes a CostReport comparing original vs optimized costs.
    """
    original = profile_workflow(workflow, gpu=gpu)
    gpu_info = GPU_PRICES.get(gpu.lower().replace("-", ""), {})
    price_per_hour = gpu_info.get("price_per_hour", 1.0)
    original_cost = calculate_cost(gpu, original.total_seconds)

    bottlenecks = find_bottlenecks(original)
    optimizations = suggest_optimizations(original)

    # Build optimized workflow
    vram_limit = gpu_info.get("vram_gb", 24.0)
    optimized_wf = apply_all_strategies(workflow, vram_limit=vram_limit)
    optimized = profile_workflow(optimized_wf, gpu=gpu)
    optimized_cost = calculate_cost(gpu, optimized.total_seconds)

    savings_usd = original_cost - optimized_cost
    savings_pct = (savings_usd / original_cost * 100) if original_cost > 0 else 0

    return CostReport(
        workflow_name=workflow.get("name", "unnamed"),
        gpu=gpu,
        original_cost=round(original_cost, 6),
        optimized_cost=round(optimized_cost, 6),
        savings_usd=round(savings_usd, 6),
        savings_pct=round(savings_pct, 1),
        bottlenecks=bottlenecks,
        optimizations=optimizations,
        original_profile=original,
        optimized_profile=optimized,
    )
