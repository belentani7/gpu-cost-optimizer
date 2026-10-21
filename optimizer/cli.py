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
from optimizer.budget import quote_workflow
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
    def cli():
        """GPU Cost Optimizer - optimize diffusion pipeline costs."""
        pass

    @cli.command()
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

    @cli.command()
    @click.argument("workflow_path", type=click.Path(exists=True))
    @click.option("--target-cost", default=0.50, type=float, help="Target cost per run in USD")
    @click.option("--gpu", default="a100", help="GPU to optimize for")
    def optimize(workflow_path: str, target_cost: float, gpu: str):
        """Optimize a workflow to meet a target cost."""
        wf = load_workflow(workflow_path)
        wf["target_gpu"] = gpu
        if target_cost <= 0:
            raise click.BadParameter("must be greater than zero", param_hint="--target-cost")
        optimized = recommend_settings(wf, target_cost=target_cost)

        original = profile_workflow(wf, gpu=gpu)
        opt_profile = profile_workflow(optimized, gpu=gpu)

        from optimizer.pricing import calculate_cost
        orig_usd = calculate_cost(gpu, original.total_seconds)
        opt_usd = calculate_cost(gpu, opt_profile.total_seconds)

        click.echo(f"\nWorkflow: {optimized.get('name', 'unnamed')}")
        click.echo(f"GPU: {gpu.upper()}")
        click.echo(f"\nOriginal:  {original.total_seconds:.3f}s  (${orig_usd:.4f})")
        click.echo(f"Optimized: {opt_profile.total_seconds:.3f}s  (${opt_usd:.4f})")
        click.echo(f"\n{savings_summary(orig_usd, opt_usd)}")
        if opt_usd > target_cost:
            click.echo(f"WARNING: estimated cost ${opt_usd:.4f} still exceeds target ${target_cost:.4f}.", err=True)

        if "scheduler" in optimized:
            sched = optimized["scheduler"]
            click.echo(f"\nScheduler: {sched.get('type', 'euler_a')} ({sched.get('steps', 30)} steps)")
        if "resolution" in optimized:
            click.echo(f"Resolution: {optimized['resolution'][0]}x{optimized['resolution'][1]}")
        if "batch_size" in optimized:
            click.echo(f"Batch size: {optimized['batch_size']}")

    @cli.command()
    @click.argument("workflow_path", type=click.Path(exists=True))
    @click.option("--gpus", default="a100,h100,l40s", help="Comma-separated GPU list")
    def compare(workflow_path: str, gpus: str):
        """Compare GPUs for a workflow."""
        wf = load_workflow(workflow_path)
        gpu_list = [g.strip().lower().replace("-", "") for g in gpus.split(",")]
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

    @cli.command()
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

    @cli.command()
    @click.argument("workflow_path", type=click.Path(exists=True, dir_okay=False))
    @click.option("--gpu", default="a100", show_default=True, help="GPU reference architecture")
    @click.option("--usd-per-hour", type=float, required=True,
                  help="Current GPU hourly rate supplied by the operator, in USD")
    @click.option("--jobs", type=int, default=1, show_default=True,
                  help="Independently billed jobs; each includes startup overhead")
    @click.option("--startup-seconds", type=float, default=0.0, show_default=True)
    @click.option("--minimum-billable-seconds", type=float, default=0.0, show_default=True)
    @click.option("--billing-quantum-seconds", type=int, default=1, show_default=True)
    @click.option("--format", "output_format", type=click.Choice(["text", "json"]),
                  default="text", show_default=True)
    def budget(workflow_path: str, gpu: str, usd_per_hour: float, jobs: int,
               startup_seconds: float, minimum_billable_seconds: float,
               billing_quantum_seconds: int, output_format: str):
        """Estimate a billed scenario using a rate YOU verify with your provider."""
        workflow = load_workflow(workflow_path)
        try:
            result = quote_workflow(
                workflow, gpu=gpu, rate_usd_hour=usd_per_hour, jobs=jobs,
                startup_seconds=startup_seconds,
                minimum_billable_seconds=minimum_billable_seconds,
                billing_quantum_seconds=billing_quantum_seconds,
            )
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        if output_format == "json":
            click.echo(json.dumps(result.json(), indent=2, ensure_ascii=False))
            return
        click.echo("\\nGPU Billing Scenario — OFFLINE HEURISTIC, not provider quote")
        click.echo(f"Workflow: {result.workflow}  |  GPU: {result.gpu.upper()}")
        click.echo(f"Operator supplied rate: ${result.user_supplied_rate_usd_hour:.4f}/GPU-hour")
        click.echo(f"Independently billed jobs: {result.jobs}")
        click.echo(f"Heuristic compute: {result.estimated_compute_seconds_each:.3f}s/job")
        click.echo(f"Boot overhead: {result.startup_seconds_each:.3f}s/job")
        click.echo(f"Minimum billing: {result.minimum_billable_seconds_each:.3f}s/job; quantum: {result.billing_quantum_seconds}s")
        click.echo(f"Billable duration: {result.billed_seconds_each:.3f}s/job")
        click.echo(f"Projected GPU compute cost: ${result.quoted_gpu_compute_usd:.6f}")
        click.echo(f"Projected invoice GPU charge: ${result.quoted_gpu_bill_usd:.6f}")
        click.echo(f"Boot + minimum/rounding overhead: ${result.startup_and_rounding_overhead_usd:.6f}")
        click.echo(f"Projected VRAM: {result.estimated_vram_gb:.2f} GB / available: {result.available_vram_gb:.0f} GB")
        click.echo(f"Heuristic VRAM fit: {'YES' if result.fits_vram_heuristic else 'NO — verify before purchasing'}")
        for warning in result.conditions:
            click.echo(f"  - {warning}")


    @cli.command(name="list-gpus")
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
        cli()


if __name__ == "__main__":
    main()
