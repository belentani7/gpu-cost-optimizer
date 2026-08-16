"""GPU pricing data and cost calculations for cloud providers."""

from __future__ import annotations

# On-demand $/hour from major cloud GPU providers (2024-2025 pricing)
GPU_PRICES: dict[str, dict[str, float]] = {
    # NVIDIA A100 80GB SXM
    "a100": {
        "price_per_hour": 2.21,
        "vram_gb": 80,
        "fp16_tflops": 312,
        "provider": "runpod",
    },
    # NVIDIA H100 SXM5
    "h100": {
        "price_per_hour": 3.70,
        "vram_gb": 80,
        "fp16_tflops": 989,
        "provider": "runpod",
    },
    # NVIDIA L40S
    "l40s": {
        "price_per_hour": 1.86,
        "vram_gb": 48,
        "fp16_tflops": 362,
        "provider": "runpod",
    },
    # RTX 4090
    "rtx4090": {
        "price_per_hour": 0.74,
        "vram_gb": 24,
        "fp16_tflops": 165,
        "provider": "runpod",
    },
    # RTX 3090
    "rtx3090": {
        "price_per_hour": 0.44,
        "vram_gb": 24,
        "fp16_tflops": 71,
        "provider": "runpod",
    },
    # NVIDIA A10G
    "a10g": {
        "price_per_hour": 0.80,
        "vram_gb": 24,
        "fp16_tflops": 125,
        "provider": "runpod",
    },
    # NVIDIA V100 16GB
    "v100": {
        "price_per_hour": 0.36,
        "vram_gb": 16,
        "fp16_tflops": 31.4,
        "provider": "runpod",
    },
}

CLOUD_PROVIDERS: dict[str, dict[str, float]] = {
    "runpod": {
        "a100": 2.21,
        "h100": 3.70,
        "l40s": 1.86,
        "rtx4090": 0.74,
        "rtx3090": 0.44,
        "a10g": 0.80,
        "v100": 0.36,
    },
    "modal": {
        "a100-80gb": 2.51,
        "a100-40gb": 1.64,
        "h100": 4.13,
        "t4": 0.16,
    },
    "lambda": {
        "a100-80gb": 2.49,
        "h100": 3.95,
        "rtx4090": 0.74,
        "rtx3090": 0.44,
    },
    "replicate": {
        "a100-80gb": 2.23,
        "a100-40gb": 1.64,
    },
}


def calculate_cost(gpu: str, seconds: float) -> float:
    """Calculate cost in USD for a given GPU and runtime in seconds.

    Args:
        gpu: GPU identifier (e.g., 'a100', 'h100').
        seconds: Runtime in seconds.

    Returns:
        Cost in USD.
    """
    gpu_lower = gpu.lower().replace("-", "").replace(" ", "")
    info = GPU_PRICES.get(gpu_lower)
    if info is None:
        raise ValueError(
            f"Unknown GPU '{gpu}'. Available: {', '.join(sorted(GPU_PRICES))}"
        )
    hours = seconds / 3600.0
    return info["price_per_hour"] * hours


def get_gpu_info(gpu: str) -> dict[str, float]:
    """Get pricing and specs for a GPU.

    Args:
        gpu: GPU identifier.

    Returns:
        Dict with price_per_hour, vram_gb, fp16_tflops, provider.
    """
    gpu_lower = gpu.lower().replace("-", "").replace(" ", "")
    info = GPU_PRICES.get(gpu_lower)
    if info is None:
        raise ValueError(
            f"Unknown GPU '{gpu}'. Available: {', '.join(sorted(GPU_PRICES))}"
        )
    return info.copy()


def list_gpus() -> list[str]:
    """Return sorted list of available GPU identifiers."""
    return sorted(GPU_PRICES.keys())
