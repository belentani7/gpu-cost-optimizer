# GPU Cost Optimizer

**Offline diffusion-workflow estimator and configuration advisor.**

This repository provides a working Python command-line tool for **simulated** GPU time, memory, and per-run cost comparisons. It does **not** connect to a GPU, run Stable Diffusion, profile CUDA kernels, deploy workloads, or measure output quality. All savings and runtimes are projections from a simplified heuristic model, **not guaranteed performance improvements**.

## Install from this repository

Prerequisites: Python 3.9+.

```bash
git clone https://github.com/belentani7/gpu-cost-optimizer.git
cd gpu-cost-optimizer
python -m pip install -e ".[dev]"
gpuopt --help
python -m pytest -q
```

No published PyPI package is assumed; install from the checked-out source as shown. This installation provides the `gpuopt` terminal command.

## Use

A complete sample workflow ships in `optimizer/workflows/character_2k.json`. Commands below are independent and produce estimations without requiring GPU hardware:

```bash
gpuopt profile optimizer/workflows/character_2k.json --gpu a100
gpuopt compare optimizer/workflows/character_2k.json --gpus a100,h100,l40s
gpuopt optimize optimizer/workflows/character_2k.json --gpu a100 --target-cost 0.50
gpuopt report optimizer/workflows/character_2k.json --gpu a100 --output estimate.md
gpuopt list-gpus-cmd
```

The report command **reads a workflow JSON**, not a previously exported measured profile. The optimize command prints a warning if its estimated cost cannot meet the target. It proposes settings but never edits the original file or deploys new model weights.

### Accepted workflow format

```json
{
  "name": "character_generation",
  "pipeline": "stable-diffusion",
  "model": "sd-xl-base",
  "scheduler": {"type": "euler_a", "steps": 50},
  "resolution": [1024, 1024],
  "batch_size": 1,
  "guidance_scale": 7.5,
  "safety_checker": true,
  "vae_tiling": false
}
```

Resolution dimensions must be positive integers up to 16384, scheduler steps between 1 and 1000, and batch size between 1 and 4096. Unsupported GPU IDs and negative runtimes are rejected.

## Accuracy and safety of estimates

- The underlying profiler computes formula-based timings from resolution, step count, batch size, and a theoretical GPU speed factor. There are **no empirical calibration benchmarks** in this repository.
- Pricing values are *historical reference inputs* (mostly from 2024–2025); they are neither live rates nor quotes from a provider. Verify current costs and billing units before making purchasing decisions.
- Changing a scheduler to LCM / turbo is a **proposal only**. It can require model-specific adapters or compatible checkpoints. A workflow JSON labeled "turbo" is not automatically runnable.
- Setting precision to FP16 is a *configuration suggestion*, not actual quantization of model weights. FP16 support and output quality depend on the model and hardware.
- Any quality-loss percentages shown in suggestions are illustrative assumptions, **not measured quality scores**. Run your own image-quality evaluation before shipping changes.
- This is a local analysis tool with a CLI, not a hosted GPU optimization SaaS. Its `docs/` page is documentation, not a live web backend.

## Development & release gate

```bash
python -m pip install -e ".[dev]"
python -m compileall -q optimizer tests
python -m pytest -q
gpuopt --help
```

Do not tag/publish a release until these commands succeed in a real Python runtime. GitHub Actions may be unavailable at an account or runner level; an unexecuted workflow is not proof of passing tests.

## License

MIT
