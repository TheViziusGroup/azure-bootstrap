# Azure Bootstrap Library

> Production-ready Azure bootstrap library for seamless integration of Azure App Configuration, Key Vault, and Application Insights into Azure Functions applications.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen.svg)]()
[![CI/CD Pipeline](https://github.com/TheViziusGroup/azure-bootstrap/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/TheViziusGroup/azure-bootstrap/actions)

## 📦 What is This Repository?

This repository contains the **source code and build configuration** for the `azure-bootstrap` pip library - a reusable bootstrap package used across 17+ Azure Functions repositories in the organization.

**Package Name**: `azure-bootstrap`
**Current Version**: `1.0.0`
**Distribution**: PyPI (public)

## 🎯 Purpose

This library solves the **circular dependency problem** between logging and configuration in Azure Functions:

- Configuration loading needs logging → But logging needs configuration → 🐔🥚
- **Our solution**: 4-phase bootstrap that provides working logging throughout the entire process

### What This Library Does

1. **Bootstrap Logging** - Logging that works immediately, before configuration loaded
2. **Configuration Loading** - Azure App Configuration with automatic Key Vault secret resolution
3. **Telemetry Setup** - Application Insights with OpenTelemetry
4. **Environment Loading** - All configs automatically loaded to `os.environ` with smart local overrides

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [API Reference](#-api-reference)
- [Migration Guide](#-migration-guide)
- [Development](#-development)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### For Library Users

```python
"""function_app.py"""
import os
import azure.functions as func
from azure_bootstrap import initialize_application, get_bootstrap_logger

_bootstrap_initialized = False
_logger = None

def _ensure_bootstrap():
    global _bootstrap_initialized, _logger
    if _bootstrap_initialized:
        return

    _logger = get_bootstrap_logger(__name__)
    config_repo = initialize_application()
    _bootstrap_initialized = True

app = func.FunctionApp()

@app.route(route="hello")
def hello(req):
    _ensure_bootstrap()
    db_host = os.getenv("DATABASE_HOST")  # All configs in os.environ
    return func.HttpResponse(f"Hello! DB: {db_host}")
```

### For Library Developers

```bash
git clone https://github.com/TheViziusGroup/azure-bootstrap
cd azure-bootstrap
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

---

## 📦 Installation

### From PyPI

```bash
pip install azure-bootstrap
```

**Add to requirements.txt**:
```text
azure-bootstrap>=1.0.0
```

---

## ⚙️ Configuration

### Option 1: Enterprise (Azure App Configuration + Key Vault)

**local.settings.json**:
```json
{
  "Values": {
    "AZURE_APP_CONFIGURATION_CONNECTION_STRING": "Endpoint=https://...;Id=...;Secret=...",
    "AZURE_KEY_VAULT_URL": "https://myvault.vault.azure.net/",
    "AZURE_APP_CONFIG_LABEL": "dev"
  }
}
```

### Option 2: Simple (Environment Variables Only)

**local.settings.json**:
```json
{
  "Values": {
    "DATABASE_HOST": "localhost",
    "DATABASE_NAME": "mydb",
    "API_KEY": "your-api-key"
  }
}
```

The library gracefully falls back to environment variables when App Configuration is not available.

### Configuration Precedence

**Priority Order** (highest to lowest):
1. **Environment variables** (`os.environ`) - Local overrides win
2. **Azure App Configuration** - Centralized config
3. **Key Vault secrets** - Secure secrets (via App Config references)
4. **Default values** - Fallback

**Example**:
```python
# local.settings.json sets: USE_MOCK_DB = "true"
# App Config has: USE_MOCK_DB = "false"
# After bootstrap: os.getenv("USE_MOCK_DB") → "true" (local wins!)
```

---

## 💡 Usage Examples

### Complete Azure Functions Example

See [examples/function_app_example.py](examples/function_app_example.py) for a production-ready example.

### Basic Usage

```python
from azure_bootstrap import initialize_application, get_bootstrap_logger

logger = get_bootstrap_logger(__name__)
config_repo = initialize_application()

# All configs now in os.environ
db_host = os.getenv("DATABASE_HOST")
```

### Custom Secrets Repository

```python
from azure_bootstrap import initialize_application, SecretsRepository

secrets_repo = SecretsRepository(vault_url="https://custom-vault.vault.azure.net/")
config_repo = initialize_application(secrets_repository=secrets_repo)
```

### Without Auto-Loading to os.environ

```python
from azure_bootstrap import create_enhanced_config_repository

config_repo = create_enhanced_config_repository(
    app_config_connection_string=conn_str,
    auto_load_to_environ=False
)

# Manually access values
db_host = config_repo.get_value("DATABASE_HOST")
```

---

## 📖 API Reference

### Main Functions

#### `initialize_application(secrets_repository=None)`
Main bootstrap function that initializes the entire application.

**Returns**: `EnhancedConfigRepository` instance

**Example**:
```python
config_repo = initialize_application()
```

#### `get_bootstrap_logger(name)`
Get a logger that works during bootstrap phase.

**Parameters**: `name` (str) - Logger name (typically `__name__`)

**Returns**: `logging.Logger`

**Example**:
```python
logger = get_bootstrap_logger(__name__)
```

#### `create_enhanced_config_repository(...)`
Create a configuration repository with App Config and Key Vault support.

**Parameters**:
- `app_config_connection_string` (str): Azure App Configuration connection string
- `secrets_repository` (optional): Custom secrets repository
- `auto_load_to_environ` (bool): Auto-load configs to os.environ

**Returns**: `EnhancedConfigRepository`

### Core Classes

- `ApplicationBootstrap` - Bootstrap orchestrator
- `EnhancedConfigRepository` - Configuration repository
- `SecretsRepository` - Key Vault secrets repository
- `TelemetryManager` - Telemetry and App Insights manager
- `BootstrapLogger` - Bootstrap logging manager

### Interfaces

All components implement interfaces for testability:
- `ApplicationBootstrapInterface`
- `EnhancedConfigRepositoryInterface`
- `SecretsRepositoryInterface`
- `TelemetryManagerInterface`
- `BootstrapLoggerInterface`

---

## 🔄 Migration Guide

### Converting Projects from Local Bootstrap Code

#### Step 1: Backup and Branch

```bash
git checkout -b backup-before-bootstrap-migration
git push origin backup-before-bootstrap-migration
git checkout -b migrate-to-bootstrap-library
```

#### Step 2: Install and Update Imports

```bash
pip install azure-bootstrap
```

```python
# BEFORE:
from src.infrastructure.application_bootstrap import initialize_application
from src.infrastructure.bootstrap_logging import get_bootstrap_logger

# AFTER:
from azure_bootstrap import initialize_application, get_bootstrap_logger
```

Find all files to update:
```bash
grep -r "from src.infrastructure" .
grep -r "from src.repositories.enhanced_config_repository" .
grep -r "from src.repositories.secrets_repository" .
```

#### Step 3: Remove Local Bootstrap Files

```bash
rm -rf src/infrastructure/
# Only remove these if you don't have app-specific extensions:
rm -f src/repositories/enhanced_config_repository.py
rm -f src/repositories/secrets_repository.py
```

#### Step 4: Update requirements.txt

```text
azure-bootstrap>=1.0.0
# Remove: azure-appconfiguration-provider, azure-keyvault-secrets,
# azure-identity, azure-monitor-opentelemetry (now included in library)
```

#### Step 5: Update Deployment Pipeline

```yaml
# In your CI/CD pipeline, just install from PyPI:
- script: pip install -r requirements.txt
```

### Migration Scenarios

| Scenario | Complexity | Time | What to Do |
|----------|-----------|------|------------|
| **Basic Function** | Easy | 15 min | Update imports, remove `src/infrastructure/` |
| **Custom Config Repository** | Medium | 30 min | Keep your custom repo, inherit from `EnhancedConfigRepository` |
| **Custom Bootstrap Logic** | Advanced | 1 hour | Keep custom bootstrap, use `initialize_application()` as foundation |
| **Custom Telemetry** | Medium | 30 min | Use `telemetry_manager.create_span()` for custom spans |

### Post-Migration Checklist

- [ ] Application starts without errors
- [ ] Bootstrap logging works
- [ ] App Configuration loads (if configured)
- [ ] Key Vault secrets resolve (if configured)
- [ ] App Insights telemetry works
- [ ] All functions work as expected

### Rollback Plan

```bash
# Revert migration
git revert <commit-hash>

# Or switch to backup branch
git checkout backup-before-bootstrap-migration
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/TheViziusGroup/azure-bootstrap
cd azure-bootstrap

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install with dev dependencies
pip install -e ".[dev]"

# Verify setup
pytest
```

### Run Tests

```bash
# All tests with coverage
pytest --cov=azure_bootstrap --cov-report=term-missing

# Specific test
pytest test/services/test_application_bootstrap.py -v

# Generate HTML coverage report
pytest --cov=azure_bootstrap --cov-report=html
open htmlcov/index.html
```

### Build Package

```bash
# Install build tools
pip install build twine

# Build wheel and source distribution
python -m build

# Output:
# dist/azure_bootstrap-1.0.0-py3-none-any.whl
# dist/azure_bootstrap-1.0.0.tar.gz

# Verify package
twine check dist/*
```

### Publish to PyPI

```bash
# Manual publish
pip install twine
twine upload dist/*

# Or automated via pipeline
git tag v1.0.0
git push origin main --tags
```

---

## 👥 Contributing

We welcome contributions! Please follow these guidelines:

### Git Workflow (Gitflow)

```
main (production)
└── dev (integration)
    ├── feature/feature-name
    ├── bugfix/bug-description
    └── hotfix/critical-fix
```

### Branch Types

- **feature/*** - New features (branch from `dev`, merge to `dev`)
- **bugfix/*** - Bug fixes (branch from `dev`, merge to `dev`)
- **hotfix/*** - Critical fixes (branch from `main`, merge to `main` AND `dev`)
- **release/*** - Release preparation (branch from `dev`, merge to `main` and `dev`)

### Quality Standards

- ✅ **Test Coverage**: Minimum 80% (90% for new code)
- ✅ **Code Style**: Black formatting, Ruff linting
- ✅ **Type Hints**: Required for all public APIs
- ✅ **Documentation**: Docstrings for all public functions
- ✅ **Commit Messages**: Conventional Commits format

### Pre-PR Checklist

```bash
# Format code
black azure_bootstrap/ test/

# Lint code
ruff check azure_bootstrap/ test/

# Type check
mypy azure_bootstrap/

# Run tests
pytest --cov=azure_bootstrap --cov-report=term-missing

# All checks must pass ✅
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines.

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Module not found
```bash
# Solution
pip install azure-bootstrap
```

#### Issue: Import errors
```python
# WRONG
from azure_bootstrap.infrastructure import initialize_application

# CORRECT
from azure_bootstrap import initialize_application
```

#### Issue: Tests failing
```bash
# Clean environment
rm -rf .venv
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[test]"
pytest
```

#### Issue: Package not found on PyPI
```bash
# Verify the package is published
pip install azure-bootstrap --verbose
```

---

## 📚 Documentation

### Core Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| **README.md** | Everyone | Complete library documentation (you are here) |
| **[CLAUDE.md](CLAUDE.md)** | AI Assistants & Developers | Development context, version history, CI/CD setup |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Contributors | Git workflow, quality standards, tooling setup, PR process |
| **LICENSE** | Everyone | License terms |

### Examples

| File | Purpose |
|------|---------|
| **[examples/function_app_example.py](examples/function_app_example.py)** | Complete Azure Functions example |
| **[examples/local.settings.json.example](examples/local.settings.json.example)** | Configuration examples |

---

## 📋 Repository Structure

```
azure-bootstrap/
├── azure_bootstrap/          # 📦 Main package (17 .py files)
│   ├── models/                   # Exception definitions
│   ├── repositories/             # Config & secrets repositories
│   └── services/                 # Bootstrap services
├── test/                         # 🧪 Test suite (80%+ coverage)
├── examples/                     # 💡 Usage examples
├── .github/workflows/ci-cd.yml   # 🔄 GitHub Actions CI/CD
├── .githooks/                    # 🪝 Git hooks (pre-commit, pre-push)
├── .vscode/                      # 💻 VS Code workspace config
├── pyproject.toml                # ⚙️ Package configuration
├── README.md                     # 👈 You are here
├── CLAUDE.md                     # 🤖 AI assistant context & version history
├── CONTRIBUTING.md               # 👥 Contribution guidelines & tooling setup
└── LICENSE                       # 📄 License file
```

---

## 🧪 Testing

### Test Coverage

- **Current**: 82% overall coverage (82.43%)
- **Requirement**: 80% minimum, 90% for new code
- **Critical Paths**: 100% coverage (bootstrap flow, config loading)

### Run Tests

```bash
pytest                           # All tests
pytest -v                        # Verbose
pytest --cov                     # With coverage
pytest test/services/ -v         # Specific directory
```

---

## 📦 Package Distribution

### What Gets Distributed

✅ Package code (17 .py files)
✅ Type hints (py.typed)
✅ LICENSE file

### What Doesn't Get Distributed

❌ Tests (test/)
❌ Examples (examples/)
❌ Development files (.gitignore, etc.)
❌ Build artifacts (dist/, build/)

See [MANIFEST.in](MANIFEST.in) for distribution control.

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The library uses GitHub Actions for continuous integration and deployment. The workflow automatically:

1. **Build & Test** - Installs dependencies, runs tests with coverage
2. **Publish** - Uploads package to PyPI (main branch and tags only)
3. **Validate** - Tests installation from feed

### Triggers

- **Push to main** → Stable release (e.g., `1.0.0`)
- **Push to develop** → Development release with timestamp (e.g., `1.0.0.dev20250124123456`)
- **Pull requests** → Build and test only (no publish)
- **Tags (v*)** → Tagged stable release

See [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) for workflow configuration.

For complete CI/CD setup instructions, see the CI/CD Setup section in [CLAUDE.md](CLAUDE.md).

---

## 📝 Version Management

### Semantic Versioning

- **Major (X.0.0)** - Breaking API changes
- **Minor (0.X.0)** - New features (backwards compatible)
- **Patch (0.0.X)** - Bug fixes

### Current Version: 1.0.0

See the Version History section in [CLAUDE.md](CLAUDE.md) for detailed changelog.

---

## 🎯 Used By

This library is used across 17+ repositories:

- AI Assistant + Vector Store Manager
- Excel Operations Processor
- Email Ingestion Service
- HITL Review Service
- ... (13 more Azure Functions projects)

---

## 📋 Requirements

### Runtime Requirements

- Python 3.11+
- Azure subscription with:
  - Azure App Configuration (optional)
  - Azure Key Vault (optional)
  - Application Insights (optional)

### Dependencies

```toml
azure-appconfiguration-provider >= 1.0.0
azure-keyvault-secrets >= 4.7.0
azure-identity >= 1.15.0
azure-monitor-opentelemetry >= 1.2.0
opentelemetry-api >= 1.22.0
opentelemetry-instrumentation-azure-functions >= 0.45b0
```

---

## ⭐ Key Benefits

### For the Organization

- ✅ **Single Source of Truth** - One codebase for 17+ projects
- ✅ **Consistent Behavior** - Same bootstrap logic everywhere
- ✅ **Easy Maintenance** - Fix bugs once, benefit everywhere
- ✅ **Version Control** - Semantic versioning with changelogs

### For Developers

- ✅ **Simple Integration** - Just `pip install` and 2-line import
- ✅ **No Implementation Knowledge** - Use public API, done
- ✅ **Type-Safe** - Full type hints for IDE support
- ✅ **Well-Tested** - 80%+ coverage, production-proven

### For Operations

- ✅ **Centralized Updates** - Deploy improvements once
- ✅ **Reduced Duplication** - No copy-paste errors
- ✅ **Better Monitoring** - Consistent telemetry
- ✅ **Easier Debugging** - Same code across projects

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🆘 Support

- **Repository**: https://github.com/TheViziusGroup/azure-bootstrap
- **Issues**: https://github.com/TheViziusGroup/azure-bootstrap/issues
- **PyPI**: https://pypi.org/project/azure-bootstrap/

---

**Ready to get started?** Install the library and see [examples/function_app_example.py](examples/function_app_example.py) for a complete working example!
