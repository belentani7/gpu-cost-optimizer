"""Stable serialization of machine-readable optimization reports."""

import json

from optimizer.analyzer import analyze_workflow
from optimizer.report import report_to_dict


def test_report_json_is_deterministic_and_excludes_internal_workflow(simple_workflow):
    report = analyze_workflow(simple_workflow, gpu="a100")

    first = report_to_dict(report)
    second = report_to_dict(report)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert "model" in first
    assert first["model"]["kind"] == "simulated"
    assert first["pricing"]["status"] == "historical_reference"
    assert "not a benchmark" in first["disclaimer"].lower()
    assert first["bottlenecks"]
    assert first["optimizations"]
    assert all("applied_workflow" not in item for item in first["optimizations"])
