"""
Service interfaces for Azure bootstrap library.

This module contains interface definitions for bootstrap services.
"""

from azure_bootstrap.services.interfaces.application_bootstrap_interface import (
    ApplicationBootstrapInterface,
)
from azure_bootstrap.services.interfaces.bootstrap_logger_interface import (
    BootstrapLoggerInterface,
)
from azure_bootstrap.services.interfaces.telemetry_manager_interface import (
    TelemetryManagerInterface,
)

__all__ = [
    "ApplicationBootstrapInterface",
    "BootstrapLoggerInterface",
    "TelemetryManagerInterface",
]
