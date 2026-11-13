"""Report generation for GPU cost optimization analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from optimizer.analyzer import Bottleneck, CostReport, Optimization
from optimizer.pricing import get_gpu_info


@dataclass
class CostReportData:
    """Report data for markdown generation."""
    workflow_name: str
    gpu: str
    original_cost: float
    optimized_cost: float
    savings_usd: float
    savings_pct: float
    bottlenecks: list[Bottleneck] = field(default_factory=list)
    optimizations: list[Optimization] = field(default_factory=list)


def report_to_dict(report: CostReportData | CostReport) -> dict:
    """Export public report fields without copying internal workflow payloads."""
    return {
        "workflow_name": report.workflow_name,
        "gpu": report.gpu,
        "original_cost": report.original_cost,
        "optimized_cost": report.optimized_cost,
        "savings_usd": report.savings_usd,
        "savings_pct": report.savings_pct,
        "bottlenecks": [asdict(item) for item in report.bottlenecks],
        "optimizations": [
            {
                "name": item.name,
                "description": item.description,
                "estimated_savings_pct": item.estimated_savings_pct,
                "estimated_savings_usd": item.estimated_savings_usd,
                "quality_impact": item.quality_impact,
            }
            for item in report.optimizations
        ],
        "model": {"kind": "simulated"},
        "pricing": {
            "status": "historical_reference",
            "currency": "USD",
            "reference_period": "2024-2025",
            "gpu": get_gpu_info(report.gpu),
        },
        "disclaimer": (
            "Simulated estimate, not a benchmark. Historical reference rates are "
            "not current provider quotes; validate actual runtime and tariffs."
        ),
    }


def to_markdown(report: CostReportData | CostReport) -> str:
    """Convert a cost report to markdown format.

    Args:
        report: CostReportData or CostReport instance.

    Returns:
        Markdown-formatted report string.
    """
    lines = [
        f"# GPU Cost Optimization Report: {report.workflow_name}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| GPU | {report.gpu.upper()} |",
        f"| Original Cost | ${report.original_cost:.4f} |",
        f"| Optimized Cost | ${report.optimized_cost:.4f} |",
        f"| Savings | ${report.savings_usd:.4f} ({report.savings_pct:.1f}%) |",
        "",
    ]

    if report.bottlenecks:
        lines.extend([
            "## Bottlenecks",
            "",
            "| Step | Time (s) | % of Total | Description |",
            "|---|---|---|---|",
        ])
        for b in report.bottlenecks:
            lines.append(
                f"| {b.step} | {b.seconds:.3f} | {b.percentage:.1f}% | {b.description} |"
            )
        lines.append("")

    if report.optimizations:
        lines.extend([
            "## Recommended Optimizations",
            "",
            "| Strategy | Savings % | Est. Cost Reduction | Quality Impact |",
            "|---|---|---|---|",
        ])
        for o in report.optimizations:
            lines.append(
                f"| {o.name} | {o.estimated_savings_pct:.1f}% | "
                f"${o.estimated_savings_usd:.4f} | {o.quality_impact} |"
            )
        lines.append("")

    return "\n".join(lines)


def savings_summary(original: float, optimized: float) -> str:
    """Generate a one-line savings summary.

    Args:
        original: Original cost in USD.
        optimized: Optimized cost in USD.

    Returns:
        Human-readable summary string.
    """
    savings = original - optimized
    pct = (savings / original * 100) if original > 0 else 0
    return (
        f"Cost reduced from ${original:.4f} to ${optimized:.4f} "
        f"(${savings:.4f} saved, {pct:.1f}% reduction)"
    )
