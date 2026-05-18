"""
Azure Bootstrap Library

A production-ready Azure bootstrap library that handles application initialization
for Azure Functions, including App Configuration, Key Vault, and App Insights integration.

This library solves the circular dependency between logging and configuration by:
1. Starting with basic console logging
2. Loading configuration from Azure App Configuration + Key Vault
3. Upgrading to App Insights telemetry when available
4. Loading all configs to os.environ for transparent access

Quick Start:
    from azure_bootstrap import initialize_application, get_bootstrap_logger

    # Get logger that works immediately
    logger = get_bootstrap_logger(__name__)

    # Bootstrap the application (App Config + Key Vault + App Insights)
    config_repo = initialize_application()

    # Now all configs are in os.environ
    db_host = os.getenv("DATABASE_HOST")

For detailed usage, see: https://github.com/TheViziusGroup/azure-bootstrap
"""

__version__ = "2.0.0"
__author__ = "The Vizius Group"
__license__ = "MIT"

# ──────────────────────────────────────────────────────────────────────────
# v2 additions (additive only — never alters the v1 surface above)
# ──────────────────────────────────────────────────────────────────────────
import logging as _stdlib_logging
import os as _os

from azure_bootstrap.bootstrap import bootstrap_initialized as bootstrap_initialized
from azure_bootstrap.bootstrap import ensure_bootstrap as ensure_bootstrap
from azure_bootstrap.bootstrap import load_local_settings as load_local_settings
from azure_bootstrap.counters import bump_counter as bump_counter
from azure_bootstrap.counters import counter_snapshot as counter_snapshot
from azure_bootstrap.exceptions import InvalidMessageError as InvalidMessageError
from azure_bootstrap.exceptions import NetworkError as NetworkError
from azure_bootstrap.exceptions import PipelineError as PipelineError
from azure_bootstrap.exceptions import RateLimitError as RateLimitError
from azure_bootstrap.exceptions import TransientError as TransientError
from azure_bootstrap.exceptions import UnrecoverableError as UnrecoverableError
from azure_bootstrap.exceptions import is_unrecoverable as is_unrecoverable
from azure_bootstrap.logging import configure_logging as configure_logging
from azure_bootstrap.logging import correlation_scope as correlation_scope
from azure_bootstrap.logging import get_correlation_id as get_correlation_id
from azure_bootstrap.logging import mask_api_key as mask_api_key
from azure_bootstrap.logging import mask_bearer_token as mask_bearer_token
from azure_bootstrap.logging import mask_email_address as mask_email_address
from azure_bootstrap.logging import mask_secrets_in_dict as mask_secrets_in_dict
from azure_bootstrap.logging import safe_json_dumps as safe_json_dumps
from azure_bootstrap.logging import sanitize_for_log as sanitize_for_log
from azure_bootstrap.logging import set_correlation_id as set_correlation_id

# Exceptions
from azure_bootstrap.models.exceptions import ConfigurationError as ConfigurationError
from azure_bootstrap.models.exceptions import KeyVaultError as KeyVaultError
from azure_bootstrap.models.exceptions import RepositoryError as RepositoryError
from azure_bootstrap.path_safety import confine_to_root as confine_to_root
from azure_bootstrap.path_safety import sanitize_path_segment as sanitize_path_segment
from azure_bootstrap.phases import PhaseResult as PhaseResult
from azure_bootstrap.phases import run_phase as run_phase
from azure_bootstrap.phases import run_phases as run_phases

# Repository implementations
from azure_bootstrap.repositories.enhanced_config_repository import (
    EnhancedConfigRepository as EnhancedConfigRepository,
)
from azure_bootstrap.repositories.enhanced_config_repository import (
    create_enhanced_config_repository as create_enhanced_config_repository,
)
from azure_bootstrap.repositories.interfaces.enhanced_config_repository_interface import (
    EnhancedConfigRepositoryInterface as EnhancedConfigRepositoryInterface,
)
from azure_bootstrap.repositories.interfaces.secrets_repository_interface import (
    SecretsRepositoryInterface as SecretsRepositoryInterface,
)
from azure_bootstrap.repositories.secrets_repository import SecretsRepository as SecretsRepository
from azure_bootstrap.security import compare_secrets as compare_secrets

# Core classes for advanced usage
# Main bootstrap function - most users only need this
from azure_bootstrap.services.application_bootstrap import (
    ApplicationBootstrap as ApplicationBootstrap,
)
from azure_bootstrap.services.application_bootstrap import (
    initialize_application as initialize_application,
)

# Bootstrap logging - works before configuration loaded
from azure_bootstrap.services.bootstrap_logging import BootstrapLogger as BootstrapLogger
from azure_bootstrap.services.bootstrap_logging import ExtraFieldsFormatter as ExtraFieldsFormatter
from azure_bootstrap.services.bootstrap_logging import (
    ensure_bootstrap_logging as ensure_bootstrap_logging,
)
from azure_bootstrap.services.bootstrap_logging import get_bootstrap_logger as get_bootstrap_logger

# Interfaces for type hinting and custom implementations
from azure_bootstrap.services.interfaces.application_bootstrap_interface import (
    ApplicationBootstrapInterface as ApplicationBootstrapInterface,
)
from azure_bootstrap.services.interfaces.bootstrap_logger_interface import (
    BootstrapLoggerInterface as BootstrapLoggerInterface,
)
from azure_bootstrap.services.interfaces.telemetry_manager_interface import (
    TelemetryManagerInterface as TelemetryManagerInterface,
)
from azure_bootstrap.services.telemetry import TelemetryManager as TelemetryManager
from azure_bootstrap.services.telemetry import telemetry_manager as telemetry_manager
from azure_bootstrap.softfail import SoftFailResult as SoftFailResult
from azure_bootstrap.softfail import soft_fail as soft_fail
from azure_bootstrap.softfail import soft_fail_with as soft_fail_with
from azure_bootstrap.tracing import latency_snapshot as latency_snapshot
from azure_bootstrap.tracing import traced as traced
from azure_bootstrap.validation import MessageSchema as MessageSchema
from azure_bootstrap.validation import queue_message_schema as queue_message_schema
from azure_bootstrap.validation import validate_message as validate_message


def refresh_setting(*names: str) -> None:
    """Re-read named settings from the cached App Configuration repo and
    write their values into ``os.environ``.

    Net-new in v2. Designed to be called from a recurring job (see
    ``azure_bootstrap.config_refresh.refresh_log_flags``) so ops can flip a
    setting in App Configuration and see it take effect within seconds
    without redeploying.

    No-ops with a DEBUG log when ``initialize_application()`` has not yet
    run. Best-effort — never raises.
    """
    if not names:
        return
    logger = _stdlib_logging.getLogger(__name__)
    try:
        from azure_bootstrap.services.application_bootstrap import (
            get_last_initialized_repo,
        )
    except Exception:
        logger.debug("refresh_setting: bootstrap module unavailable")
        return
    repo = get_last_initialized_repo()
    if repo is None:
        logger.debug("refresh_setting: no cached repo (initialize_application not called)")
        return
    for name in names:
        if not isinstance(name, str) or not name:
            continue
        try:
            value = repo.get_value(name)
        except Exception as exc:
            logger.warning("refresh_setting: failed to read %s: %s", name, exc)
            continue
        if value is None:
            continue
        _os.environ[name] = str(value)


# Public API
__all__ = [
    # Version
    "__version__",
    # Main bootstrap functions (most common usage)
    "initialize_application",
    "get_bootstrap_logger",
    "create_enhanced_config_repository",
    "ensure_bootstrap_logging",
    # Singleton instance
    "telemetry_manager",
    # Core classes
    "ApplicationBootstrap",
    "BootstrapLogger",
    "ExtraFieldsFormatter",
    "TelemetryManager",
    "EnhancedConfigRepository",
    "SecretsRepository",
    # Interfaces
    "ApplicationBootstrapInterface",
    "BootstrapLoggerInterface",
    "TelemetryManagerInterface",
    "EnhancedConfigRepositoryInterface",
    "SecretsRepositoryInterface",
    # Exceptions
    "RepositoryError",
    "ConfigurationError",
    "KeyVaultError",
    # v2 additions — Tier 1 always-on primitives
    "bootstrap_initialized",
    "bump_counter",
    "configure_logging",
    "correlation_scope",
    "counter_snapshot",
    "ensure_bootstrap",
    "get_correlation_id",
    "latency_snapshot",
    "load_local_settings",
    "mask_api_key",
    "mask_bearer_token",
    "mask_email_address",
    "mask_secrets_in_dict",
    "refresh_setting",
    "safe_json_dumps",
    "sanitize_for_log",
    "set_correlation_id",
    "traced",
    # v2 Parts 2+3 — exceptions, soft-fail, phases, validation, path safety, security
    "InvalidMessageError",
    "MessageSchema",
    "NetworkError",
    "PhaseResult",
    "PipelineError",
    "RateLimitError",
    "SoftFailResult",
    "TransientError",
    "UnrecoverableError",
    "compare_secrets",
    "confine_to_root",
    "is_unrecoverable",
    "queue_message_schema",
    "run_phase",
    "run_phases",
    "sanitize_path_segment",
    "soft_fail",
    "soft_fail_with",
    "validate_message",
]
