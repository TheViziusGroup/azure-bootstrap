"""Built-in transport factories: console and App Insights.

Registered into the transport registry at import time. Each factory returns a
``logging.Handler`` (or ``None`` to signal "transport unavailable", a soft
no-op the registry treats as not-enabled).
"""

from __future__ import annotations

import logging

from azure_bootstrap.logging.correlation import CorrelationFilter
from azure_bootstrap.logging.formatter import ExtraFieldsFormatter

_CONSOLE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def make_console_handler() -> logging.Handler:
    """Console transport — the same stack ``configure_logging()`` installs.

    Use the console transport as an *alternative* to ``configure_logging()``'s
    handler. Enabling both produces two console handlers (duplicate lines).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(ExtraFieldsFormatter(_CONSOLE_FORMAT))
    handler.addFilter(CorrelationFilter())
    return handler


def make_app_insights_handler() -> logging.Handler | None:
    """App Insights transport — delegates to the v1 ``TelemetryManager``.

    ``configure_azure_monitor()`` attaches its own OpenTelemetry ``LoggingHandler``
    to the root logger. We reuse that machinery (no duplication) and return the
    attached handler so the registry can later *detach* it on disable.

    Returns ``None`` when telemetry is unavailable or no connection string is
    configured — i.e. App Insights could not be turned on. Note the limitation:
    disabling only detaches the OpenTelemetry handler from the root logger; it
    does not tear down the underlying exporter started by
    ``configure_azure_monitor()``.
    """
    try:
        from azure_bootstrap.services import telemetry as _telemetry
    except Exception:
        return None

    if not getattr(_telemetry, "TELEMETRY_AVAILABLE", False):
        return None

    root = logging.getLogger()
    before = set(root.handlers)
    try:
        _telemetry.telemetry_manager.configure(allow_reconfigure=True)
    except Exception:
        return None

    # configure_azure_monitor attaches its LoggingHandler to root. Locate the
    # newly added handler so the registry owns add/remove from here on.
    added = [h for h in root.handlers if h not in before]
    for handler in added:
        # The registry adds the returned handler itself; remove it here to keep
        # a single attachment owned by the registry.
        root.removeHandler(handler)
    if added:
        return added[-1]

    # No handler was added (already configured, or OTel attaches elsewhere).
    # Nothing for the registry to own — treat as a soft no-op.
    return None


def _register_builtins() -> None:
    from azure_bootstrap.transports import register_transport
    from azure_bootstrap.transports.sumologic import make_sumo_logic_handler

    register_transport("console", make_console_handler, replace=True)
    register_transport("app_insights", make_app_insights_handler, replace=True)
    register_transport("sumo_logic", make_sumo_logic_handler, replace=True)
