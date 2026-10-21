"""Regression tests for the installed gpuopt Click entrypoint.

The original command group was overwritten by a second function named main,
so both `gpuopt --help` and all profile/optimize commands failed at startup.
"""
import sys

import pytest
from click.testing import CliRunner

from optimizer.cli import cli, main


def test_commands_are_registered_under_click_group():
    assert {"profile", "optimize", "compare", "report", "list-gpus"} <= set(cli.commands)


def test_help_and_gpu_listing_execute():
    runner = CliRunner()
    help_result = runner.invoke(cli, ["--help"])
    assert help_result.exit_code == 0, help_result.output
    assert "profile" in help_result.output
    assert "list-gpus" in help_result.output
    prices_result = runner.invoke(cli, ["list-gpus"])
    assert prices_result.exit_code == 0, prices_result.output
    assert "A100" in prices_result.output


def test_installed_console_entrypoint_calls_click_without_recursion(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["gpuopt", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_example_workflow_profiles_offline():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "examples" / "workflow.json"
    result = CliRunner().invoke(cli, ["profile", str(path), "--gpu", "a100"])
    assert result.exit_code == 0, result.output
    assert "example_character_generation" in result.output
