# gpu-cost-optimizer

Optimize GPU compute costs in diffusion pipelines by up to 70%.

Measures workflow compute time on cloud GPUs and adjusts scheduler steps, resolution, and batch size to minimize cost while maintaining acceptable quality.

## Installation

```bash
pip install gpu-cost-optimizer
```

Or from source:

```bash
git clone https://github.com/your-org/gpu-cost-optimizer.git
cd gpu-cost-optimizer
pip install -e ".[dev]"
```

## Quick Start

```bash
# Profile a workflow on a specific GPU
gpuopt profile workflow.json --gpu a100

# Optimize to meet a target cost
gpuopt optimize workflow.json --target-cost 0.50

# Compare across GPUs
gpuopt compare workflow.json --gpus a100,h100,l40s

# Generate a report
gpuopt report profile.json --output report.md
```

## Workflow JSON Format

```json
{
  "name": "character_generation",
  "pipeline": "stable-diffusion",
  "model": "sd-xl-base",
  "scheduler": {
    "type": "euler_a",
    "steps": 50
  },
  "resolution": [1024, 1024],
  "batch_size": 1,
  "guidance_scale": 7.5,
  "safety_checker": true,
  "vae_tiling": false
}
```

## Optimization Strategies

| Strategy | Typical Savings | Quality Impact |
|---|---|---|
| Reduce scheduler steps | 40-60% | Minimal with turbo schedulers |
| Lower resolution | 20-50% | Depends on target use |
| Optimize batch size | 10-30% | None |
| Turbo scheduler swap | 30-50% | Minor |
| Model quantization (FP16) | 25-40% | Negligible |

## GPU Pricing Reference

Realistic on-demand pricing from major cloud providers (USD/hour):

| GPU | VRAM | Typical Price |
|---|---|---|
| NVIDIA A100 80GB | 80 GB | $2.21 |
| NVIDIA H100 80GB | 80 GB | $3.70 |
| NVIDIA L40S | 48 GB | $1.86 |
| RTX 4090 | 24 GB | $0.74 |
| RTX 3090 | 24 GB | $0.44 |
| A10G | 24 GB | $0.80 |

## License

MIT
