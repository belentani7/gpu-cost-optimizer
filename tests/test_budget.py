"""Budget scenario regression — hourly rates are always explicit, never stale defaults."""
from __future__ import annotations

import json
import math

import pytest
from click.testing import CliRunner

from optimizer.budget import quote_workflow
from optimizer.cli import cli


@pytest.fixture
def example_workflow():
    return {
        "name": "sample_2026", "scheduler": {"type": "euler_a", "steps": 35},
        "resolution": [1024, 1024], "batch_size": 1, "safety_checker": True
    }


def test_quoted_bill_accounts_for_minimum_boot_and_each_independent_job(example_workflow):
    plan = quote_workflow(
        example_workflow, gpu="a100", rate_usd_hour=3.60,
        jobs=20, startup_seconds=45, minimum_billable_seconds=60,
        billing_quantum_seconds=60,
    )
    assert plan.user_supplied_rate_usd_hour == 3.60
    assert plan.billed_seconds_each == 60
    assert plan.jobs == 20
    assert plan.quoted_gpu_bill_usd == pytest.approx(1.2)
    assert plan.quoted_gpu_compute_usd < plan.quoted_gpu_bill_usd
    assert plan.startup_and_rounding_overhead_usd > 0
    assert plan.source.startswith("explicit-user-rate")
    assert plan.currency == "USD"
    assert plan.fits_vram_heuristic


def test_billing_rounds_per_job_not_after_aggregating(example_workflow):
    one = quote_workflow(example_workflow, gpu="h100", rate_usd_hour=1.0,
                         jobs=1, billing_quantum_seconds=60)
    five = quote_workflow(example_workflow, gpu="h100", rate_usd_hour=1.0,
                          jobs=5, billing_quantum_seconds=60)
    assert one.billed_seconds_each == five.billed_seconds_each
    assert five.total_billed_hours == pytest.approx(one.total_billed_hours * 5)
    assert five.quoted_gpu_bill_usd == pytest.approx(one.quoted_gpu_bill_usd * 5)


@pytest.mark.parametrize("kwargs", [
    {"rate_usd_hour": float("nan")},
    {"rate_usd_hour": float("inf")},
    {"rate_usd_hour": -1},
    {"rate_usd_hour": 0},
    {"rate_usd_hour": True},
    {"rate_usd_hour": 1, "jobs": 0},
    {"rate_usd_hour": 1, "jobs": 1.5},
    {"rate_usd_hour": 1, "startup_seconds": -1},
    {"rate_usd_hour": 1, "minimum_billable_seconds": float("inf")},
    {"rate_usd_hour": 1, "billing_quantum_seconds": 0},
])
def test_budget_rejects_unsafe_inputs(example_workflow, kwargs):
    with pytest.raises(ValueError):
        quote_workflow(example_workflow, gpu="a100", **kwargs)


def test_cli_budget_disallows_implicit_historical_gpu_price(tmp_path, example_workflow):
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(example_workflow), encoding="utf-8")
    runner = CliRunner()
    missing = runner.invoke(cli, ["budget", str(path)])
    assert missing.exit_code != 0
    assert "Missing option" in missing.output
    invalid = runner.invoke(cli, ["budget", str(path), "--usd-per-hour", "-1"])
    assert invalid.exit_code != 0
    assert "greater than zero" in invalid.output


def test_cli_budget_emits_parseable_json_and_mentions_all_exclusions(tmp_path, example_workflow):
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(example_workflow), encoding="utf-8")
    result = CliRunner().invoke(cli, [
        "budget", str(path), "--gpu", "a100", "--usd-per-hour", "3.20",
        "--startup-seconds", "30", "--jobs", "100", "--format", "json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["jobs"] == 100
    assert data["user_supplied_rate_usd_hour"] == 3.2
    assert data["quoted_gpu_bill_usd"] >= data["quoted_gpu_compute_usd"]
    assert "taxes" in " ".join(data["conditions"]).lower()
