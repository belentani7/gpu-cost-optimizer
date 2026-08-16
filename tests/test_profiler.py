"""Tests for workflow profiling."""

from optimizer.profiler import (
    ProfileResult,
    StepTiming,
    estimate_total_cost,
    load_workflow,
    measure_step_times,
    profile_workflow,
)
from optimizer.pricing import calculate_cost


class TestMeasureStepTimes:
    def test_returns_five_steps(self, simple_workflow):
        times = measure_step_times(simple_workflow)
        assert len(times) == 5

    def test_all_positive(self, simple_workflow):
        times = measure_step_times(simple_workflow)
        assert all(t > 0 for t in times)

    def test_denoise_is_longest(self, simple_workflow):
        times = measure_step_times(simple_workflow)
        step_names = ["vae_encode", "text_encode", "denoise", "vae_decode", "safety_check"]
        denoise_idx = step_names.index("denoise")
        assert times[denoise_idx] == max(times)

    def test_larger_resolution_takes_longer(self, simple_workflow, large_workflow):
        t_small = measure_step_times(simple_workflow)
        t_large = measure_step_times(large_workflow)
        assert sum(t_large) > sum(t_small)

    def test_more_steps_take_longer(self, simple_workflow):
        wf = simple_workflow.copy()
        wf["scheduler"] = {"type": "euler_a", "steps": 100}
        t_short = measure_step_times(simple_workflow)
        t_long = measure_step_times(wf)
        assert sum(t_long) > sum(t_short)

    def test_batch_size_scales(self, simple_workflow):
        wf = simple_workflow.copy()
        wf["batch_size"] = 4
        t_single = measure_step_times(simple_workflow)
        t_batch = measure_step_times(wf)
        assert sum(t_batch) > sum(t_single)


class TestProfileWorkflow:
    def test_returns_profile_result(self, simple_workflow):
        result = profile_workflow(simple_workflow, gpu="a100")
        assert isinstance(result, ProfileResult)
        assert result.workflow_name == "test_workflow"
        assert result.gpu == "a100"

    def test_has_step_timings(self, simple_workflow):
        result = profile_workflow(simple_workflow, gpu="a100")
        assert len(result.steps) == 5
        assert all(isinstance(s, StepTiming) for s in result.steps)

    def test_total_seconds_matches_steps(self, simple_workflow):
        result = profile_workflow(simple_workflow, gpu="a100")
        expected = sum(s.elapsed_seconds for s in result.steps)
        assert abs(result.total_seconds - expected) < 0.01

    def test_vram_estimate_is_positive(self, simple_workflow):
        result = profile_workflow(simple_workflow, gpu="a100")
        assert result.vram_limit_gb > 0

    def test_different_gpus_give_different_times(self, simple_workflow):
        r1 = profile_workflow(simple_workflow, gpu="a100")
        r2 = profile_workflow(simple_workflow, gpu="rtx3090")
        # RTX 3090 is slower, so total time should differ
        assert r1.total_seconds != r2.total_seconds

    def test_step_times_property(self, simple_workflow):
        result = profile_workflow(simple_workflow, gpu="a100")
        assert result.step_times == [s.elapsed_seconds for s in result.steps]


class TestEstimateTotalCost:
    def test_positive_cost(self, simple_workflow):
        profile = profile_workflow(simple_workflow, gpu="a100")
        pricing = {"a100": 2.21}
        cost = estimate_total_cost(profile, pricing)
        assert cost > 0

    def test_scales_with_time(self, simple_workflow):
        profile = profile_workflow(simple_workflow, gpu="a100")
        pricing = {"a100": 2.21}
        cost = estimate_total_cost(profile, pricing)
        # Double the time should double the cost
        profile.total_seconds *= 2
        cost2 = estimate_total_cost(profile, pricing)
        assert abs(cost2 - cost * 2) < 0.001


class TestCalculateCost:
    def test_one_hour(self):
        cost = calculate_cost("a100", 3600)
        assert abs(cost - 2.21) < 0.01

    def test_half_hour(self):
        cost = calculate_cost("a100", 1800)
        assert abs(cost - 1.105) < 0.01

    def test_various_gpus(self):
        c1 = calculate_cost("a100", 3600)
        c2 = calculate_cost("h100", 3600)
        assert c2 > c1  # H100 costs more

    def test_unknown_gpu_raises(self):
        import pytest
        with pytest.raises(ValueError):
            calculate_cost("nonexistent_gpu", 100)


class TestLoadWorkflow:
    def test_load_workflow(self, tmp_path):
        import json
        wf = {"name": "test", "resolution": [512, 512]}
        p = tmp_path / "wf.json"
        p.write_text(json.dumps(wf))
        loaded = load_workflow(p)
        assert loaded["name"] == "test"

    def test_missing_file_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_workflow("nonexistent.json")
