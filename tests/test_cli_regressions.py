"""End-to-end smoke tests for the executable Click command surface."""

import json
import subprocess
import sys

import pytest
from click.testing import CliRunner

from optimizer.cli import cli
from optimizer.pricing import calculate_cost
from optimizer.profiler import load_workflow, profile_workflow
from optimizer.strategies import reduce_steps


@pytest.fixture
def workflow_file(tmp_path, simple_workflow):
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(simple_workflow), encoding="utf-8")
    return path


def test_help_starts_via_package_module():
    result = subprocess.run(
        [sys.executable, "-m", "optimizer.cli", "--help"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "profile" in result.stdout
    assert "optimize" in result.stdout
    assert "compare" in result.stdout
    assert "report" in result.stdout


def test_profile_reads_real_workflow_file(workflow_file):
    result = CliRunner().invoke(cli, ["profile", str(workflow_file), "--gpu", "a100"])
    assert result.exit_code == 0, result.output
    assert "test_workflow" in result.output
    assert "Step breakdown:" in result.output


def test_compare_command_lists_asked_gpus(workflow_file):
    result = CliRunner().invoke(cli, ["compare", str(workflow_file), "--gpus", "a100,h100"])
    assert result.exit_code == 0, result.output
    assert "A100" in result.output
    assert "H100" in result.output
    assert "RTX3090" not in result.output


def test_report_creates_markdown(workflow_file, tmp_path):
    path = tmp_path / "report.md"
    result = CliRunner().invoke(cli, ["report", str(workflow_file), "--output", str(path)])
    assert result.exit_code == 0, result.output
    assert path.exists()
    assert "GPU Cost Optimization Report" in path.read_text(encoding="utf-8")


def test_optimize_rejects_zero_budget(workflow_file):
    result = CliRunner().invoke(cli, ["optimize", str(workflow_file), "--target-cost", "0"])
    assert result.exit_code != 0
    assert "must be greater than zero" in result.output


@pytest.mark.parametrize("resolution", [[0, 512], [-1, 512], [512], ["512", 512], [512, 16385]])
def test_rejects_bad_resolution(simple_workflow, resolution):
    simple_workflow["resolution"] = resolution
    with pytest.raises(ValueError, match="resolution"):
        profile_workflow(simple_workflow)


@pytest.mark.parametrize("steps", [0, -5, 1.5, True, 1001])
def test_rejects_bad_steps(simple_workflow, steps):
    simple_workflow["scheduler"]["steps"] = steps
    with pytest.raises(ValueError, match="steps"):
        profile_workflow(simple_workflow)


@pytest.mark.parametrize("batch", [0, -1, 1.2, True, 4097])
def test_rejects_bad_batch(simple_workflow, batch):
    simple_workflow["batch_size"] = batch
    with pytest.raises(ValueError, match="batch_size"):
        profile_workflow(simple_workflow)


def test_no_silent_default_for_unknown_gpu(simple_workflow):
    with pytest.raises(ValueError, match="Unknown GPU"):
        profile_workflow(simple_workflow, gpu="unknown")


def test_reducing_steps_does_not_increase_steps(simple_workflow):
    simple_workflow["scheduler"]["steps"] = 6
    for threshold in (0.01, 0.05, 0.10, 0.50):
        result = reduce_steps(simple_workflow, max_quality_loss=threshold)
        assert 1 <= result["scheduler"]["steps"] <= 6
    assert simple_workflow["scheduler"]["steps"] == 6


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf")])
def test_cost_rejects_invalid_seconds(seconds):
    with pytest.raises(ValueError, match="Runtime"):
        calculate_cost("a100", seconds)


def test_load_workflow_rejects_nonobject(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_workflow(path)
