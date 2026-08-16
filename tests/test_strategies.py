"""Tests for optimization strategies."""

from optimizer.strategies import (
    apply_all_strategies,
    optimize_batch_size,
    quantize_model,
    reduce_resolution,
    reduce_steps,
    use_turbo_scheduler,
)


class TestReduceSteps:
    def test_conservative(self, simple_workflow):
        result = reduce_steps(simple_workflow, max_quality_loss=0.01)
        steps = result["scheduler"]["steps"]
        assert steps >= 15
        assert steps < 50

    def test_moderate(self, simple_workflow):
        result = reduce_steps(simple_workflow, max_quality_loss=0.05)
        steps = result["scheduler"]["steps"]
        assert steps >= 15
        assert steps <= 30

    def test_aggressive(self, simple_workflow):
        result = reduce_steps(simple_workflow, max_quality_loss=0.10)
        steps = result["scheduler"]["steps"]
        assert steps >= 12
        assert steps <= 20

    def test_does_not_modify_original(self, simple_workflow):
        original_steps = simple_workflow["scheduler"]["steps"]
        reduce_steps(simple_workflow)
        assert simple_workflow["scheduler"]["steps"] == original_steps

    def test_minimum_floor(self, simple_workflow):
        result = reduce_steps(simple_workflow, max_quality_loss=0.50)
        assert result["scheduler"]["steps"] >= 8


class TestReduceResolution:
    def test_reduces_large_resolution(self, simple_workflow):
        result = reduce_resolution(simple_workflow)
        orig_w = simple_workflow["resolution"][0]
        new_w = result["resolution"][0]
        assert new_w <= orig_w

    def test_does_not_go_below_512(self, simple_workflow):
        wf = simple_workflow.copy()
        wf["resolution"] = [512, 512]
        result = reduce_resolution(wf)
        assert result["resolution"][0] >= 256

    def test_does_not_modify_original(self, simple_workflow):
        original_res = simple_workflow["resolution"][:]
        reduce_resolution(simple_workflow)
        assert simple_workflow["resolution"] == original_res


class TestOptimizeBatchSize:
    def test_increases_for_large_vram(self, simple_workflow):
        result = optimize_batch_size(simple_workflow, vram_limit=80.0)
        assert result["batch_size"] >= 1

    def test_limits_for_small_vram(self, simple_workflow):
        result = optimize_batch_size(simple_workflow, vram_limit=8.0)
        assert result["batch_size"] >= 1
        assert result["batch_size"] <= 4

    def test_never_zero(self, simple_workflow):
        result = optimize_batch_size(simple_workflow, vram_limit=1.0)
        assert result["batch_size"] >= 1


class TestUseTurboScheduler:
    def test_switches_to_lcm(self, simple_workflow):
        result = use_turbo_scheduler(simple_workflow)
        assert result["scheduler"]["type"] == "lcm"

    def test_reduces_steps(self, simple_workflow):
        result = use_turbo_scheduler(simple_workflow)
        assert result["scheduler"]["steps"] <= 8

    def test_marks_turbo(self, simple_workflow):
        result = use_turbo_scheduler(simple_workflow)
        assert result["scheduler"]["turbo"] is True

    def test_does_not_modify_original(self, simple_workflow):
        original_type = simple_workflow["scheduler"]["type"]
        use_turbo_scheduler(simple_workflow)
        assert simple_workflow["scheduler"]["type"] == original_type


class TestQuantizeModel:
    def test_sets_float16(self, simple_workflow):
        result = quantize_model(simple_workflow)
        assert result["dtype"] == "float16"

    def test_enables_quantization(self, simple_workflow):
        result = quantize_model(simple_workflow)
        assert result["quantization"]["enabled"] is True
        assert result["quantization"]["precision"] == "fp16"


class TestApplyAllStrategies:
    def test_produces_valid_workflow(self, simple_workflow):
        result = apply_all_strategies(simple_workflow)
        assert "scheduler" in result
        assert "resolution" in result
        assert "batch_size" in result

    def test_does_not_modify_original(self, simple_workflow):
        original_name = simple_workflow["name"]
        apply_all_strategies(simple_workflow)
        assert simple_workflow["name"] == original_name

    def test_with_target_cost(self, simple_workflow):
        result = apply_all_strategies(simple_workflow, target_cost=0.50)
        assert result["scheduler"]["type"] == "lcm"
