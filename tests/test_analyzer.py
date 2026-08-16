"""Tests for cost analysis and bottleneck detection."""

from optimizer.analyzer import (
    Bottleneck,
    CostReport,
    Optimization,
    analyze_workflow,
    find_bottlenecks,
    suggest_optimizations,
)
from optimizer.profiler import ProfileResult, StepTiming
from optimizer.report import CostReportData, savings_summary, to_markdown


class TestFindBottlenecks:
    def _make_profile(self, times: dict[str, float], gpu: str = "a100") -> ProfileResult:
        steps = [StepTiming(step_name=k, elapsed_seconds=v) for k, v in times.items()]
        total = sum(s.elapsed_seconds for s in steps)
        return ProfileResult(
            workflow_name="test", gpu=gpu, steps=steps, total_seconds=total
        )

    def test_detects_denoise_bottleneck(self):
        profile = self._make_profile({
            "vae_encode": 0.1,
            "text_encode": 0.05,
            "denoise": 5.0,
            "vae_decode": 0.2,
            "safety_check": 0.05,
        })
        bottlenecks = find_bottlenecks(profile)
        names = [b.step for b in bottlenecks]
        assert "denoise" in names

    def test_empty_profile(self):
        profile = ProfileResult(workflow_name="empty", gpu="a100")
        bottlenecks = find_bottlenecks(profile)
        assert bottlenecks == []

    def test_sorted_by_time(self):
        profile = self._make_profile({
            "vae_encode": 1.0,
            "text_encode": 0.5,
            "denoise": 10.0,
            "vae_decode": 2.0,
            "safety_check": 0.1,
        })
        bottlenecks = find_bottlenecks(profile)
        for i in range(len(bottlenecks) - 1):
            assert bottlenecks[i].seconds >= bottlenecks[i + 1].seconds


class TestSuggestOptimizations:
    def _make_profile(self, gpu: str = "a100") -> ProfileResult:
        steps = [
            StepTiming(step_name="vae_encode", elapsed_seconds=0.2),
            StepTiming(step_name="text_encode", elapsed_seconds=0.1),
            StepTiming(step_name="denoise", elapsed_seconds=4.0),
            StepTiming(step_name="vae_decode", elapsed_seconds=0.3),
            StepTiming(step_name="safety_check", elapsed_seconds=0.05),
        ]
        return ProfileResult(
            workflow_name="test", gpu=gpu, steps=steps, total_seconds=4.65
        )

    def test_returns_optimizations(self):
        profile = self._make_profile()
        opts = suggest_optimizations(profile)
        assert len(opts) > 0
        assert all(isinstance(o, Optimization) for o in opts)

    def test_turbo_scheduler_suggestion(self):
        profile = self._make_profile()
        opts = suggest_optimizations(profile)
        names = [o.name for o in opts]
        assert "Turbo Scheduler (LCM)" in names

    def test_fp16_suggestion(self):
        profile = self._make_profile()
        opts = suggest_optimizations(profile)
        names = [o.name for o in opts]
        assert "FP16 Quantization" in names


class TestAnalyzeWorkflow:
    def test_returns_cost_report(self, simple_workflow):
        report = analyze_workflow(simple_workflow, gpu="a100")
        assert isinstance(report, CostReport)
        assert report.workflow_name == "test_workflow"
        assert report.original_cost > 0
        assert report.optimized_cost > 0

    def test_savings_are_positive(self, simple_workflow):
        report = analyze_workflow(simple_workflow, gpu="a100")
        assert report.savings_usd >= 0
        assert report.savings_pct >= 0

    def test_has_bottlenecks(self, simple_workflow):
        report = analyze_workflow(simple_workflow, gpu="a100")
        assert len(report.bottlenecks) > 0

    def test_has_optimizations(self, simple_workflow):
        report = analyze_workflow(simple_workflow, gpu="a100")
        assert len(report.optimizations) > 0


class TestCostReportData:
    def test_to_markdown(self, simple_workflow):
        report = analyze_workflow(simple_workflow, gpu="a100")
        data = CostReportData(
            workflow_name=report.workflow_name,
            gpu=report.gpu,
            original_cost=report.original_cost,
            optimized_cost=report.optimized_cost,
            savings_usd=report.savings_usd,
            savings_pct=report.savings_pct,
            bottlenecks=report.bottlenecks,
            optimizations=report.optimizations,
        )
        md = to_markdown(data)
        assert "# GPU Cost Optimization Report" in md
        assert "test_workflow" in md
        assert "Bottlenecks" in md

    def test_savings_summary(self):
        s = savings_summary(1.0, 0.5)
        assert "$1.0000" in s
        assert "$0.5000" in s
        assert "50.0%" in s

    def test_savings_summary_zero_original(self):
        s = savings_summary(0.0, 0.0)
        assert "0.0%" in s
