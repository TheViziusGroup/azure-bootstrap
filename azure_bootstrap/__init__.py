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

__version__ = "1.0.0"
__author__ = "The Vizius Group"
__license__ = "MIT"

# Exceptions
from azure_bootstrap.models.exceptions import ConfigurationError as ConfigurationError
from azure_bootstrap.models.exceptions import KeyVaultError as KeyVaultError
from azure_bootstrap.models.exceptions import RepositoryError as RepositoryError

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
]
