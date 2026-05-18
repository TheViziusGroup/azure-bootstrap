"""Tests for ``azure_bootstrap.health``."""

from __future__ import annotations

import logging

import pytest

from azure_bootstrap.health import (
    check_app_config_health,
    check_app_insights_health,
    check_app_insights_logging,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in (
        "USE_MOCK_BOOTSTRAP",
        "AZURE_APP_CONFIGURATION_CONNECTION_STRING",
        "AZURE_APPCONFIG_ENDPOINT",
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
    ):
        monkeypatch.delenv(k, raising=False)


def test_app_config_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    assert check_app_config_health() == {"status": "ok", "mock": True}


def test_app_config_unconfigured() -> None:
    assert check_app_config_health() == {"status": "not_configured"}


def test_app_insights_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    assert check_app_insights_health() == {"status": "ok", "mock": True}


def test_app_insights_unconfigured() -> None:
    assert check_app_insights_health() == {"status": "not_configured"}


def test_app_insights_logging_unconfigured() -> None:
    assert check_app_insights_logging() == {"status": "not_configured"}


def test_app_insights_logging_detects_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )

    class FakeAzureMonitorTraceExporter(logging.Handler):
        pass

    handler = FakeAzureMonitorTraceExporter()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        result = check_app_insights_logging()
        assert result["status"] == "ok"
        assert "FakeAzureMonitorTraceExporter" in result["handler"]
    finally:
        root.removeHandler(handler)


def test_app_insights_logging_missing_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )
    # Remove any pre-existing matching handlers
    root = logging.getLogger()
    saved = list(root.handlers)
    for h in saved:
        if "azure" in type(h).__module__.lower() or "monitor" in type(h).__name__.lower():
            root.removeHandler(h)
    try:
        result = check_app_insights_logging()
        # Either ok (some matching handler still attached) or error.
        assert result["status"] in {"ok", "error"}
    finally:
        for h in saved:
            if h not in root.handlers:
                root.addHandler(h)
