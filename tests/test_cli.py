"""El CLI debe mostrar el disclaimer obligatorio en --help."""

from __future__ import annotations

from typer.testing import CliRunner

from habitalens import DISCLAIMER
from habitalens.cli import app

runner = CliRunner()


def test_root_help_shows_disclaimer() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "no representa ni sustituye" in result.stdout
    assert "caracter oficial ni fehaciente" in result.stdout


def test_resolve_help_shows_disclaimer() -> None:
    result = runner.invoke(app, ["resolve", "--help"])
    assert result.exit_code == 0
    assert DISCLAIMER[:40] in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "habitalens" in result.stdout
