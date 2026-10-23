import math

import pytest

from optimizer.recommender import compare_gpus, recommend_gpu, recommend_settings


def test_compare_gpus_evaluates_available_gpus(simple_workflow):
    comparisons = compare_gpus(simple_workflow)

    assert comparisons
    assert {comparison.gpu for comparison in comparisons}
    assert all(comparison.estimated_cost >= 0 for comparison in comparisons)


def test_recommend_gpu_returns_available_gpu(simple_workflow):
    recommendation = recommend_gpu(simple_workflow, budget=1.0)

    assert recommendation


def test_recommend_gpu_rejects_budget_too_low_instead_of_overrunning(simple_workflow):
    with pytest.raises(ValueError, match="minimum"):
        recommend_gpu(simple_workflow, budget=0.000000000001)


def test_recommend_gpu_never_proposes_insufficient_vram(simple_workflow):
    # The estimate exceeds even the 80 GB models in the comparison catalog.
    huge = {**simple_workflow, "resolution": [16384, 16384], "batch_size": 2}
    assert not any(c.meets_vram for c in compare_gpus(huge))
    with pytest.raises(ValueError, match="VRAM"):
        recommend_gpu(huge, budget=100_000.0)


@pytest.mark.parametrize("invalid_budget", [0, -1, float("nan"), float("inf"), -float("inf")])
def test_recommender_rejects_invalid_budget(simple_workflow, invalid_budget):
    with pytest.raises(ValueError, match="finite|positive"):
        recommend_gpu(simple_workflow, invalid_budget)


def test_recommendation_is_always_feasible_and_within_budget(simple_workflow):
    budget = 10.0
    selected = recommend_gpu(simple_workflow, budget=budget)
    rows = {row.gpu: row for row in compare_gpus(simple_workflow)}
    assert rows[selected].meets_vram
    assert rows[selected].estimated_cost <= budget


@pytest.mark.parametrize("invalid_target", [0, -1, float("nan"), float("inf")])
def test_settings_refuse_invalid_cost_target(simple_workflow, invalid_target):
    with pytest.raises(ValueError, match="finite|greater than zero"):
        recommend_settings(simple_workflow, invalid_target)


def test_settings_keep_original_when_cost_already_meets_target(simple_workflow):
    import copy
    original = copy.deepcopy(simple_workflow)
    result = recommend_settings(simple_workflow, target_cost=100.0)
    assert result == original
    assert simple_workflow == original


def test_settings_never_increase_short_dimension_during_budget_reduction(simple_workflow):
    workflow = {**simple_workflow, "resolution": [512, 128]}
    result = recommend_settings(workflow, target_cost=1e-10)
    assert result["resolution"][0] <= 512
    assert result["resolution"][1] <= 128
    assert workflow["resolution"] == [512, 128]
