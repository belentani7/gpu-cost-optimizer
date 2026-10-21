"""Executable CLI regression tests for the installed gpuopt entry point."""

import sys

import pytest
from click.testing import CliRunner

from optimizer.cli import cli, main


def test_console_entrypoint_displays_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["gpuopt", "--help"])
    with pytest.raises(SystemExit) as stopped:
        main()
    assert stopped.value.code == 0
    output = capsys.readouterr().out
    assert "GPU Cost Optimizer" in output
    assert "profile" in output
    assert "compare" in output


@pytest.mark.parametrize(
    "command",
    ["profile", "optimize", "compare", "report", "list-gpus"],
)
def test_expected_subcommands_are_registered(command):
    result = CliRunner().invoke(cli, [command, "--help"])
    assert result.exit_code == 0, result.output


def test_profile_sample_workflow_from_cli():
    result = CliRunner().invoke(cli, [
        "profile", "optimizer/workflows/character_2k.json", "--gpu", "a100"
    ])
    assert result.exit_code == 0, result.output
    assert "Total time:" in result.output


def test_gpu_catalog():
    result = CliRunner().invoke(cli, ["list-gpus"])
    assert result.exit_code == 0, result.output
    assert "A100" in result.output
