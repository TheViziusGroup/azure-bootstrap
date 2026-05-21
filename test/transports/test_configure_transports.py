"""configure_transports: code params, env-flag fallback, precedence, idempotency."""

from __future__ import annotations

import logging
import os

from azure_bootstrap.transports import configure_transports, list_transports


def _console_handlers() -> int:
    from azure_bootstrap.transports import _active

    return 1 if "console" in _active else 0


def test_code_param_on_off() -> None:
    configure_transports(console=True)
    assert list_transports()["console"]["enabled"] is True
    configure_transports(console=False)
    assert list_transports()["console"]["enabled"] is False


def test_env_flag_fallback_disables_console() -> None:
    os.environ["CONSOLE_LOGGING_ENABLED"] = "0"
    configure_transports()  # no explicit param -> env wins
    assert list_transports()["console"]["enabled"] is False


def test_env_flag_default_console_on() -> None:
    configure_transports()  # nothing set -> console default True
    assert list_transports()["console"]["enabled"] is True


def test_code_param_overrides_env() -> None:
    os.environ["CONSOLE_LOGGING_ENABLED"] = "1"
    configure_transports(console=False)  # explicit False beats env "1"
    assert list_transports()["console"]["enabled"] is False


def test_sumo_enabled_via_env(monkeypatch) -> None:
    os.environ["SUMO_LOGIC_COLLECTOR_URL"] = "https://example.test/receiver"
    os.environ["SUMO_LOGIC_LOGGING_ENABLED"] = "1"
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: _fake_resp())
    configure_transports()
    try:
        assert list_transports()["sumo_logic"]["enabled"] is True
    finally:
        configure_transports(sumo_logic=False)


def test_idempotent_rerun_single_handler() -> None:
    configure_transports(console=True)
    root = logging.getLogger()
    n = len(root.handlers)
    configure_transports(console=True)
    configure_transports(console=True)
    assert len(root.handlers) == n
    assert _console_handlers() == 1


class _fake_resp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
