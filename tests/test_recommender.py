from optimizer.recommender import compare_gpus, recommend_gpu


def test_compare_gpus_evaluates_available_gpus(simple_workflow):
    comparisons = compare_gpus(simple_workflow)

    assert comparisons
    assert {comparison.gpu for comparison in comparisons}
    assert all(comparison.estimated_cost >= 0 for comparison in comparisons)


def test_recommend_gpu_returns_available_gpu(simple_workflow):
    recommendation = recommend_gpu(simple_workflow, budget=1.0)

    assert recommendation
