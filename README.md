# Azure Bootstrap Library

> Production-ready Azure bootstrap library for seamless integration of Azure App Configuration, Key Vault, and Application Insights into Azure Functions applications.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)]()
[![CI/CD Pipeline](https://github.com/TheViziusGroup/azure-bootstrap/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/TheViziusGroup/azure-bootstrap/actions)

## 📦 What is This Repository?

This repository contains the **source code and build configuration** for the `azure-bootstrap` pip library - a reusable bootstrap package used across 17+ Azure Functions repositories in the organization.

**Package Name**: `azure-bootstrap`
**Current Version**: `2.0.0`
**Distribution**: PyPI (public)

## 🎯 Purpose

v1 solved the **logging ↔ configuration circular dependency** for Azure
Functions apps. v2 expands that into the **entire cross-cutting layer**
every Vizius Azure project used to re-implement on top of v1.

### What v1 does (still works unchanged)

1. **Bootstrap Logging** — works immediately, before configuration loads
2. **Configuration Loading** — Azure App Configuration + Key Vault
3. **Telemetry Setup** — Application Insights via OpenTelemetry
4. **Environment Loading** — all configs auto-loaded to `os.environ`

### What v2 adds (additive, opt-in via pip extras)

- **Structured logging** with `ExtraFieldsFormatter`, correlation IDs
  via `correlation_scope`, secret/email/control-char masking,
  noisy-logger silencing
- **Tracing** — `@traced` decorator with latency histograms, slow-budget
  alerts, sensitive-arg masking, async auto-detection
- **Tiered alerts** — `alert_dev_team` with WARN / ERROR / CRITICAL,
  dedup + rate-limit + escalation, `install_global_exception_hooks`
- **Error vocabulary** — `PipelineError` → `UnrecoverableError` /
  `TransientError` with `is_unrecoverable(exc)` classifier; soft-fail
  + per-phase guards
- **Ingress hardening** — 4-gate attachment classifier (extension →
  MIME → size → magic-byte), zip-bomb defense, PDF action stripping,
  bidi-stripping filename sanitizer + root confinement
- **Service Bus consumer** — `handle_message` with dead-letter-vs-abandon
  routing, `lock_for_process` covering long-running handlers
- **Webhook + auth** — `install_graph_webhook_route` with validation
  handshake, clientState verification, dedup, rate limit
- **AI usage tracker** — tokens + cost across sliding windows, soft TPM
  cap, threshold-based CRITICAL alerts
- **Operational** — health probes, FastAPI middleware, heartbeat +
  consumer watchdog, dynamic log-level refresh, DLQ digest with
  HMAC-signed resubmit tokens, `/api/metrics` aggregator

See [CHANGELOG.md](CHANGELOG.md) for the full v2 surface and
[MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md) for the adoption order.

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

### v2 — production-grade logging in 30 seconds

```python
from azure_bootstrap.alerts import install_global_exception_hooks, register_dispatcher
from azure_bootstrap.bootstrap import ensure_bootstrap
from azure_bootstrap.logging import configure_logging


def my_email_sender(recipients, subject, html_body):
    ...  # any callable matching this signature


configure_logging()
install_global_exception_hooks()
ensure_bootstrap()
register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])
```

Every line emitted via stdlib `logging` now carries correlation IDs, extra
fields render as greppable `key=repr(value)` pairs, noisy third-party loggers
are silenced, and uncaught exceptions fire CRITICAL alerts (with dedup +
rate-limit + escalation). See [MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md)
for the full extras matrix.

### For Library Users (v1 surface, still works unchanged)

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

### Base (Tier 1 always-on, stdlib-only)

```bash
pip install azure-bootstrap
```

```text
# requirements.txt
azure-bootstrap>=2.0,<3
```

### With opt-in extras

| Extra | Pulls | When you need |
| --- | --- | --- |
| `[alerts]` | stdlib only | Tiered alert dispatcher + global excepthooks |
| `[health]` | core deps | App Config + App Insights health probes |
| `[fastapi]` | `fastapi` | Request middleware, webhook route, rate-limit dep |
| `[heartbeat]` | stdlib only | Background heartbeat + consumer watchdog |
| `[config-refresh]` | stdlib only | Dynamic `LOG_LEVEL` refresh via App Config |
| `[servicebus]` | `azure-servicebus` | DLQ digest, growth alarm, consumer wrapper, sb_lock |
| `[openai]` | stdlib only | AI usage tracker (SDK-agnostic) |
| `[tokens]` | stdlib only | HMAC action tokens |
| `[scheduler]` | `apscheduler` | NCRONTAB parser |
| `[metrics]` | stdlib only | `/api/metrics` aggregator |
| `[retry]` | `tenacity` | Pre-configured retry wrappers |
| `[ingress]` | stdlib only | 4-gate attachment classifier |
| `[pdf-safety]` | `pypdf` | PDF action stripping |
| `[ratelimit]` | stdlib only | TokenBucket |
| `[notify]` | stdlib only | Two-tier notification builders + throttle |
| `[subscription]` | stdlib only | Renewal loop pattern |
| `[identity]` | core deps | `build_credential` (Workload Identity preferred) |
| `[auth]` | (pair with `[fastapi]`) | Graph webhook + API-key helpers |
| `[sb-lock]` | (pair with `[servicebus]`) | Message lock auto-renewer |
| `[audit]` | stdlib only | Audit-log conventions |
| `[failclose]` | stdlib only | Env-var fail-closed-vs-open helpers |
| `[all]` | everything above | All extras at once |

```bash
# Common combinations
pip install 'azure-bootstrap[alerts,fastapi,health]'
pip install 'azure-bootstrap[servicebus,sb-lock,retry,heartbeat]'
pip install 'azure-bootstrap[all]'
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

The full examples library lives in [examples/](examples/) — 37 numbered
single-concept files plus 3 end-to-end app templates. Each example is
runnable with `USE_MOCK_BOOTSTRAP=true` (no real Azure needed) and ends
with a `# ── Expected output ──` block.

Start here:

| File | Concept |
| --- | --- |
| [examples/01_quickstart.py](examples/01_quickstart.py) | 30-second setup |
| [examples/03_correlation_scope.py](examples/03_correlation_scope.py) | Correlation IDs across nested calls |
| [examples/04_traced_decorator.py](examples/04_traced_decorator.py) | `@traced` sync + async |
| [examples/09_soft_fail.py](examples/09_soft_fail.py) | Degraded-result pattern |
| [examples/15_ingress_classifier.py](examples/15_ingress_classifier.py) | 4-gate attachment pipeline |
| [examples/21_consumer_wrapper.py](examples/21_consumer_wrapper.py) | Service Bus handler |
| [examples/27_alerts_dispatcher.py](examples/27_alerts_dispatcher.py) | Tiered alerts |
| [examples/e2e_azure_function.py](examples/e2e_azure_function.py) | Full Azure Function (v2) |
| [examples/e2e_fastapi_pipeline.py](examples/e2e_fastapi_pipeline.py) | Full FastAPI app |
| [examples/e2e_aks_sb_worker.py](examples/e2e_aks_sb_worker.py) | Full AKS Service Bus consumer |

See [examples/README.md](examples/README.md) for the full index +
reading order + per-example pip-extra requirements.

### v1 basic usage (still supported unchanged)

```python
from azure_bootstrap import initialize_application, get_bootstrap_logger

logger = get_bootstrap_logger(__name__)
config_repo = initialize_application()

# All configs now in os.environ
db_host = os.getenv("DATABASE_HOST")
```

---

## 📖 API Reference

The library exports ~40 top-level symbols and 30+ subpackages. Rather
than duplicating the spec here, each module's public surface is documented
in three places:

- **Module docstrings** — every `azure_bootstrap/<module>/__init__.py`
  opens with a docstring explaining the module's purpose and invariants.
- **Per-symbol runnable examples** — [examples/](examples/) covers every
  public function with at least one focused demo (see the table above).
- **[CHANGELOG.md](CHANGELOG.md)** — the v2.0.0 entry catalogs every
  new public symbol, organized by tier.

### v1 surface (preserved byte-identical)

The original 20 entries in v1's `__all__` are still exported with the
same signatures and behavior. See
[`azure_bootstrap/__init__.py`](azure_bootstrap/__init__.py) for the
authoritative list. The four most-used:

- `initialize_application(secrets_repository=None)` → `EnhancedConfigRepository`
- `get_bootstrap_logger(name)` → `logging.Logger`
- `create_enhanced_config_repository(app_config_connection_string, ...)` → `EnhancedConfigRepository`
- `telemetry_manager` — the singleton `TelemetryManager` instance

### v2 top-level re-exports (additive)

The most common v2 primitives are re-exported from the top-level
namespace for ergonomic import:

```python
from azure_bootstrap import (
    # Logging
    configure_logging, correlation_scope, get_correlation_id, set_correlation_id,
    mask_api_key, mask_email_address, mask_secrets_in_dict, sanitize_for_log,
    # Tracing + counters
    traced, latency_snapshot, bump_counter, counter_snapshot,
    # Bootstrap
    ensure_bootstrap, bootstrap_initialized, load_local_settings, refresh_setting,
    # Exception hierarchy
    PipelineError, UnrecoverableError, TransientError,
    InvalidMessageError, RateLimitError, NetworkError, is_unrecoverable,
    # Soft-fail + phases + validation
    soft_fail, soft_fail_with, SoftFailResult,
    run_phase, run_phases, PhaseResult,
    validate_message, MessageSchema, queue_message_schema,
    # Path / security
    sanitize_path_segment, confine_to_root, compare_secrets,
)
```

Everything else is reachable via its subpackage (e.g.
`from azure_bootstrap.alerts import alert_dev_team`).

---

## 🔄 Migration Guide

### v1 → v2

**TL;DR**: Pin `azure-bootstrap>=2.0,<3`. No code changes needed —
v1 imports keep working. The full migration document is
[MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md), including the suggested
adoption order for v2 primitives, the extras matrix, and the small list
of behavior changes to be aware of (notably: `DEBUG_LOGGING_ENABLED` is
now a required second factor for DEBUG output).

### Converting a project off in-repo `src/infrastructure/` to azure-bootstrap

The original v0 → v1 migration (extracting bootstrap code out of a
project's `src/infrastructure/`) is preserved in git history at the
`1.0.0` tag — see the `Migration Guide` section of that revision's
README if you're maintaining a legacy app that hasn't crossed the
boundary yet.

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
# dist/azure_bootstrap-2.0.0-py3-none-any.whl
# dist/azure_bootstrap-2.0.0.tar.gz

# Verify package
twine check dist/*
```

### Publish to PyPI

```bash
# Manual publish
pip install twine
twine upload dist/*

# Or automated via pipeline (preferred — uses OIDC Trusted Publisher)
git tag v2.0.0
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

- ✅ **Test Coverage**: Minimum 85% (90% for new code) — raised at v2.0.0
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
| **README.md** | Everyone | Library overview (you are here) |
| **[CHANGELOG.md](CHANGELOG.md)** | Everyone | Complete release-by-release surface |
| **[MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md)** | v1 adopters | v1 → v2 upgrade path + adoption order |
| **[examples/README.md](examples/README.md)** | New adopters | Reading order through ~40 runnable examples |
| **[CLAUDE.md](CLAUDE.md)** | AI Assistants & Developers | Development context, version history, CI/CD setup |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Contributors | Git workflow, quality standards, tooling setup, PR process |
| **LICENSE** | Everyone | License terms |

### Examples

The [examples/](examples/) directory contains a flat, numbered library
of single-concept files plus three end-to-end app templates. Every
numbered file is self-contained — drop one into your project as a
starting point. See [examples/README.md](examples/README.md) for the
full index.

---

## 📋 Repository Structure

```
azure-bootstrap/
├── azure_bootstrap/                  # 📦 Main package
│   ├── __init__.py                       # Public API surface (v1 + v2)
│   ├── py.typed                          # PEP 561 type-hint marker
│   │
│   │   v1 (preserved unchanged)
│   ├── models/                           # ConfigurationError / RepositoryError / KeyVaultError
│   ├── repositories/                     # App Config + Key Vault loaders + interfaces
│   ├── services/                         # ApplicationBootstrap, BootstrapLogger, TelemetryManager
│   │
│   │   v2 Tier 1 (always-on, stdlib only)
│   ├── logging/                          # configure_logging, formatter, masking, correlation, noise
│   ├── tracing/                          # @traced, latency histograms, slow thresholds
│   ├── counters/                         # bump_counter, counter_snapshot
│   ├── bootstrap/                        # ensure_bootstrap, load_local_settings
│   ├── exceptions/                       # PipelineError tree + is_unrecoverable
│   ├── softfail/                         # soft_fail, soft_fail_with
│   ├── phases/                           # run_phase, run_phases
│   ├── validation/                       # queue_message_schema, validate_message
│   ├── path_safety/                      # sanitize_path_segment, confine_to_root
│   ├── security/                         # compare_secrets, verify_api_key_header
│   ├── identity/                         # build_credential, credential_health
│   ├── audit/                            # build_audit_extra
│   ├── failclose/                        # require_env, optional_env, fail_open_env
│   │
│   │   v2 Tier 2 (opt-in extras)
│   ├── alerts/                           # alert_dev_team + dispatcher + escalation + render
│   ├── health/                           # check_app_config_health / app_insights / handler-detect
│   ├── fastapi_middleware/               # install_middleware (request timing + 5xx alerts)
│   ├── heartbeat/                        # background heartbeat + consumer watchdog
│   ├── config_refresh/                   # refresh_log_flags
│   ├── retry/                            # build_retry, retry_azure_transient, retry_ai_transient
│   ├── ingress/                          # 4-gate attachment classifier
│   ├── ratelimit/                        # TokenBucket + presets
│   ├── notify/                           # two-tier notification builders + sender throttle
│   ├── subscription/                     # ensure_resource + renewal_loop
│   ├── auth/                             # install_graph_webhook_route + WebhookDedup
│   │
│   │   v2 Tier 3 (advanced opt-in)
│   ├── servicebus/                       # handle_message + DLQ digest + growth alarm + tokens
│   ├── openai/                           # AI usage tracker (SDK-agnostic)
│   ├── tokens/                           # issue/verify_action_token (HMAC-SHA256)
│   ├── scheduler/                        # parse_cron_trigger (NCRONTAB)
│   ├── metrics/                          # build_metrics_snapshot
│   ├── pdf_safety/                       # sanitize_pdf_for_passthrough
│   └── sb_lock/                          # lock_for_process, ManagedLock
│
├── test/                                 # 🧪 Test suite (423 tests, 87.07% coverage)
├── examples/                             # 💡 Examples library — see examples/README.md
├── .github/workflows/ci-cd.yml           # 🔄 GitHub Actions CI/CD
├── .githooks/                            # 🪝 Git hooks (pre-commit, pre-push)
├── .vscode/                              # 💻 VS Code workspace config
├── pyproject.toml                        # ⚙️ Package metadata + ~20 optional extras
├── README.md                             # 👈 You are here
├── CHANGELOG.md                          # 📋 Full release surface
├── MIGRATING-FROM-V1.md                  # 🔀 v1 → v2 adoption guide
├── CLAUDE.md                             # 🤖 AI assistant context + CI/CD ops
├── CONTRIBUTING.md                       # 👥 Contribution guidelines + tooling
└── LICENSE                               # 📄 MIT
```

---

## 🧪 Testing

### Test Coverage

- **Current**: 87.07% overall, 423 passing tests
- **Requirement**: 85% minimum (raised from 80% at v2.0.0), 90% new code
- **Critical Paths**: 100% coverage (bootstrap flow, exception classifier, alert dispatcher)

### Run Tests

```bash
pytest                           # All tests
pytest -v                        # Verbose
pytest --cov                     # With coverage
pytest test/alerts/ -v           # Specific subpackage
pytest test/tracing/ -v          # Another subpackage
```

The test suite uses `AZURE_BOOTSTRAP_ALLOW_RESET=1` (set automatically
via `test/conftest.py`) to gate the library's test-only `reset_state()`
helpers. Don't set this in production.

---

## 📦 Package Distribution

### What Gets Distributed

✅ Package code (`azure_bootstrap/` — ~70 .py files across 30+ subpackages)
✅ Type hints (`py.typed` marker)
✅ LICENSE file

### What Doesn't Get Distributed

❌ Tests (`test/`)
❌ Examples (`examples/`)
❌ Development files (.gitignore, .githooks/, .vscode/, etc.)
❌ Build artifacts (`dist/`, `build/`, `htmlcov/`)

See [MANIFEST.in](MANIFEST.in) for distribution control.

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The library uses GitHub Actions for continuous integration and deployment. The workflow automatically:

1. **Build & Test** - Installs dependencies, runs tests with coverage
2. **Publish** - Uploads package to PyPI (main branch and tags only)
3. **Validate** - Tests installation from feed

### Triggers

- **Push to main** → Stable release (e.g., `2.0.0`)
- **Push to develop** → Development release with timestamp (e.g., `2.0.0.dev20260518123456`)
- **Pull requests** → Build and test only (no publish)
- **Tags (v*)** → Tagged stable release

See [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) for workflow configuration.

For complete CI/CD setup instructions, see the CI/CD Setup section in [CLAUDE.md](CLAUDE.md).

---

## 📝 Version Management

### Semantic Versioning

- **Major (X.0.0)** — Breaking API changes
- **Minor (0.X.0)** — New features (backwards compatible)
- **Patch (0.0.X)** — Bug fixes

### Current Version: 2.0.0

v2.0.0 is **strictly additive** over v1 — every v1 public symbol is
preserved byte-identical. See [CHANGELOG.md](CHANGELOG.md) for the full
release surface and [MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md) for the
adoption order.

---

## 🎯 Used By

This library is used across 17+ Azure Functions / FastAPI / AKS-worker
repositories at Vizius — payroll ingestion, NETA report generation,
email-driven document pipelines, HITL review tooling, vector store
managers, and more.

---

## 📋 Requirements

### Runtime Requirements

- Python 3.11+
- Azure subscription with (any/all optional):
  - Azure App Configuration
  - Azure Key Vault
  - Application Insights
  - Azure Service Bus
  - Azure OpenAI / Microsoft Graph

### Core Dependencies (always installed)

```toml
azure-appconfiguration-provider >= 1.0.0
azure-keyvault-secrets >= 4.7.0
azure-identity >= 1.15.0
azure-monitor-opentelemetry >= 1.2.0
opentelemetry-api >= 1.22.0

# Pinned for CVE remediation:
azure-core >= 1.38.0      # CVE-2026-21226
filelock >= 3.20.3        # CVE-2025-68146, CVE-2026-22701
urllib3 >= 2.6.3          # CVE-2026-21441
```

Optional extras pull additional runtime deps only when installed —
see the **Installation** table near the top of this file for the full
matrix.

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

**Ready to get started?** `pip install azure-bootstrap`, then open
[examples/01_quickstart.py](examples/01_quickstart.py) for the
30-second setup and [examples/README.md](examples/README.md) for the
full reading order.
