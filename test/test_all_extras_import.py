"""Smoke-test that every optional extra imports cleanly when installed."""

from __future__ import annotations

import importlib

import pytest


def _import(module: str) -> None:
    importlib.import_module(module)


@pytest.mark.parametrize(
    "module",
    [
        "azure_bootstrap.transports.adx",
        "azure_bootstrap.transports.event_hubs",
        "azure_bootstrap.transports.panther",
        "azure_bootstrap.transports.blob",
        "azure_bootstrap.transports.sql",
        "azure_bootstrap.transports.nosql",
        "azure_bootstrap.db",
        "azure_bootstrap.db.migrations",
        "azure_bootstrap.db.outbox",
        "azure_bootstrap.email",
        "azure_bootstrap.http",
        "azure_bootstrap.http.async_client",
        "azure_bootstrap.documentdb",
        "azure_bootstrap.aks",
        "azure_bootstrap.aks.leader_election",
        "azure_bootstrap.governance",
        "azure_bootstrap.auth.hmac",
        "azure_bootstrap.servicebus.async_ext",
        "azure_bootstrap.contrib.scaffold",
    ],
)
def test_v3_modules_import(module: str) -> None:
    _import(module)


def test_all_transport_factories_soft_noop() -> None:
    from azure_bootstrap.transports.adx import make_adx_handler
    from azure_bootstrap.transports.blob import make_blob_handler
    from azure_bootstrap.transports.event_hubs import make_event_hubs_handler
    from azure_bootstrap.transports.nosql import make_nosql_handler
    from azure_bootstrap.transports.panther import make_panther_handler
    from azure_bootstrap.transports.sql import make_sql_handler
    from azure_bootstrap.transports.sumologic import make_sumo_logic_handler

    assert make_adx_handler() is None
    assert make_event_hubs_handler() is None
    assert make_blob_handler() is None
    assert make_nosql_handler() is None
    assert make_panther_handler() is None
    assert make_sql_handler() is None
    assert make_sumo_logic_handler() is None


def test_version_matches_pyproject() -> None:
    """``__version__`` must agree with ``[project] version``.

    The version is hand-maintained in two places, and CI's dev-build step
    rewrites both. Pinning a literal here just broke every release; asserting
    the two copies agree tests the invariant that actually matters — and needs
    no edit at release time.
    """
    import tomllib
    from pathlib import Path

    import azure_bootstrap as ab

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject.open("rb") as fh:
        declared = tomllib.load(fh)["project"]["version"]

    assert ab.__version__ == declared


def test_top_level_v3_exports() -> None:
    import azure_bootstrap as ab

    for name in (
        "configure_transports",
        "build_session",
        "AcsEmailSender",
        "build_info",
        "drain_outbox",
    ):
        assert hasattr(ab, name), f"missing top-level export: {name}"

    from azure_bootstrap.aks.leader_election import LeaderElection
    from azure_bootstrap.servicebus.async_ext import ReplayGuard

    assert LeaderElection is not None
    assert ReplayGuard is not None
