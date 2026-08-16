"""CLI interface for gpu-cost-optimizer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import click
except ImportError:
    click = None  # type: ignore[assignment]

from optimizer.analyzer import analyze_workflow
from optimizer.pricing import GPU_PRICES, list_gpus
from optimizer.profiler import load_workflow, profile_workflow
from optimizer.recommender import compare_gpus, recommend_gpu, recommend_settings
from optimizer.report import CostReportData, savings_summary, to_markdown


def _require_click():
    if click is None:
        print("Error: 'click' is required. Install with: pip install click", file=sys.stderr)
        sys.exit(1)


if click is not None:

    @click.group()
    def main():
        """GPU Cost Optimizer - optimize diffusion pipeline costs."""
        pass

    @main.command()
    @click.argument("workflow_path", type=click.Path(exists=True))
    @click.option("--gpu", default="a100", help="GPU to profile on (default: a100)")
    def profile(workflow_path: str, gpu: str):
        """Profile a workflow on a specific GPU."""
        wf = load_workflow(workflow_path)
        result = profile_workflow(wf, gpu=gpu)

        click.echo(f"\nWorkflow: {result.workflow_name}")
        click.echo(f"GPU: {result.gpu.upper()}")
        click.echo(f"Total time: {result.total_seconds:.3f}s")
        click.echo(f"Est. VRAM: {result.vram_limit_gb:.1f} GB\n")

        click.echo("Step breakdown:")
        for s in result.steps:
            pct = (s.elapsed_seconds / result.total_seconds * 100) if result.total_seconds > 0 else 0
            click.echo(f"  {s.step_name:16s} {s.elapsed_seconds:.4f}s  ({pct:.1f}%)")

    @main.command()
    @click.argument("workflow_path", type=click.Path(exists=True))
    @click.option("--target-cost", default=0.50, type=float, help="Target cost per run in USD")
    @click.option("--gpu", default="a100", help="GPU to optimize for")
    def optimize(workflow_path: str, target_cost: float, gpu: str):
        """Optimize a workflow to meet a target cost."""
        wf = load_workflow(workflow_path)
        wf["target_gpu"] = gpu
        optimized = recommend_settings(wf, target_cost=target_cost)

        original = profile_workflow(wf, gpu=gpu)
        opt_profile = profile_workflow(optimized, gpu=gpu)

        orig_cost = GPU_PRICES.get(gpu.lower().replace("-", ""), {}).get("price_per_hour", 1.0)
        from optimizer.pricing import calculate_cost
        orig_usd = calculate_cost(gpu, original.total_seconds)
        opt_usd = calculate_cost(gpu, opt_profile.total_seconds)

        click.echo(f"\nWorkflow: {optimized.get('name', 'unnamed')}")
        click.echo(f"GPU: {gpu.upper()}")
        click.echo(f"\nOriginal:  {original.total_seconds:.3f}s  (${orig_usd:.4f})")
        click.echo(f"Optimized: {opt_profile.total_seconds:.3f}s  (${opt_usd:.4f})")
        click.echo(f"\n{savings_summary(orig_usd, opt_usd)}")

        if "scheduler" in optimized:
            sched = optimized["scheduler"]
            click.echo(f"\nScheduler: {sched.get('type', 'euler_a')} ({sched.get('steps', 30)} steps)")
        if "resolution" in optimized:
            click.echo(f"Resolution: {optimized['resolution'][0]}x{optimized['resolution'][1]}")
        if "batch_size" in optimized:
            click.echo(f"Batch size: {optimized['batch_size']}")

    @main.command()
    @click.argument("workflow_path", type=click.Path(exists=True))
    @click.option("--gpus", default="a100,h100,l40s", help="Comma-separated GPU list")
    def compare(workflow_path: str, gpus: str):
        """Compare GPUs for a workflow."""
        wf = load_workflow(workflow_path)
        gpu_list = [g.strip() for g in gpus.split(",")]
        comparisons = compare_gpus(wf)
        comparisons = [c for c in comparisons if c.gpu in gpu_list]

        click.echo(f"\nGPU Comparison: {wf.get('name', 'unnamed')}\n")
        click.echo(f"{'GPU':<10} {'Price/hr':>10} {'Time':>10} {'Cost':>10} {'VRAM OK':>10}")
        click.echo("-" * 52)
        for c in comparisons:
            vram_ok = "Yes" if c.meets_vram else "NO"
            click.echo(
                f"{c.gpu.upper():<10} ${c.price_per_hour:>8.2f} "
                f"{c.estimated_time_seconds:>8.3f}s "
                f"${c.estimated_cost:>8.4f} {vram_ok:>10}"
            )

    @main.command()
    @click.argument("profile_path", type=click.Path(exists=True))
    @click.option("--output", "-o", default=None, help="Output file path")
    @click.option("--gpu", default="a100", help="GPU for analysis")
    def report(profile_path: str, output: str | None, gpu: str):
        """Generate a cost optimization report."""
        with open(profile_path, "r", encoding="utf-8") as f:
            wf = json.load(f)
        result = analyze_workflow(wf, gpu=gpu)
        report_data = CostReportData(
            workflow_name=result.workflow_name,
            gpu=result.gpu,
            original_cost=result.original_cost,
            optimized_cost=result.optimized_cost,
            savings_usd=result.savings_usd,
            savings_pct=result.savings_pct,
            bottlenecks=result.bottlenecks,
            optimizations=result.optimizations,
        )
        md = to_markdown(report_data)

        if output:
            Path(output).write_text(md, encoding="utf-8")
            click.echo(f"Report written to {output}")
        else:
            click.echo(md)

    @main.command()
    def list_gpus_cmd():
        """List available GPUs and pricing."""
        click.echo("\nAvailable GPUs:\n")
        click.echo(f"{'GPU':<12} {'Price/hr':>10} {'VRAM':>8} {'TFLOPS':>10}")
        click.echo("-" * 42)
        for gpu_id in list_gpus():
            info = GPU_PRICES[gpu_id]
            click.echo(
                f"{gpu_id.upper():<12} ${info['price_per_hour']:>8.2f} "
                f"{info['vram_gb']:>5.0f}GB {info['fp16_tflops']:>8.1f}"
            )


def main():
    """Entry point."""
    _require_click()
    if click is not None:
        main.__wrapped__()  # type: ignore[attr-defined]
