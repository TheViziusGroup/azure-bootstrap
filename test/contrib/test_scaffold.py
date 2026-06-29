"""Scaffold CLI tests."""

from __future__ import annotations

from pathlib import Path

from azure_bootstrap.contrib.scaffold import list_templates, main, scaffold


def test_list_templates_includes_helm() -> None:
    names = list_templates()
    assert any(n.startswith("helm/") for n in names)


def test_scaffold_substitutes_vars(tmp_path: Path) -> None:
    dest = scaffold(
        "helm/worker/Chart.yaml.template",
        tmp_path,
        {"app_name": "my-worker"},
    )
    assert dest.read_text().count("my-worker") >= 1


def test_main_version() -> None:
    assert main(["version"]) == 0
