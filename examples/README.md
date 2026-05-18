# azure-bootstrap v2 examples

A flat, numbered, copy-paste-friendly library of v2 usage examples. Each
numbered file demonstrates one concept and runs in isolation; every file
is self-contained (no shared helpers) so you can drop one into your
project and it works.

## 30-second quick start

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

See [01_quickstart.py](01_quickstart.py) for a runnable version with a
mock sender.

## Running the examples

```bash
# Most examples short-circuit Azure calls in mock mode:
export USE_MOCK_BOOTSTRAP=true

# Some examples reset shared state (counters, latency histograms);
# the library gates resets behind this env var as a safety mechanism:
export AZURE_BOOTSTRAP_ALLOW_RESET=1

# Run any example directly:
python examples/01_quickstart.py
```

## Reading order

The files are numbered roughly by how foundational they are — start at
01 and read until you stop seeing relevant patterns.

| #  | File | Use this if you need to … |
| -- | ---- | ------------------------- |
| 01 | [01_quickstart.py](01_quickstart.py) | Set up a brand-new project with production-grade defaults in 30 seconds |
| 02 | [02_structured_logging.py](02_structured_logging.py) | Format extras as greppable `key=repr` pairs; mask secrets/emails/control chars at the call site |
| 03 | [03_correlation_scope.py](03_correlation_scope.py) | Propagate correlation IDs across nested sync + async calls |
| 04 | [04_traced_decorator.py](04_traced_decorator.py) | Add latency + alert-on-error to any function with one decorator |
| 05 | [05_slow_thresholds.py](05_slow_thresholds.py) | Get a WARN alert when an operation breaches its time budget |
| 06 | [06_counters.py](06_counters.py) | Track best-effort observability counts across threads |
| 07 | [07_local_settings.py](07_local_settings.py) | Use `local.settings.json` for dev without overriding existing env |
| 08 | [08_exception_hierarchy.py](08_exception_hierarchy.py) | Classify pipeline errors as "dead-letter this" vs "retry me" |
| 09 | [09_soft_fail.py](09_soft_fail.py) | Continue with a degraded result when an optional sub-feature breaks |
| 10 | [10_phases.py](10_phases.py) | Run a multi-stage pipeline where one stage's bug must not nuke the rest |
| 11 | [11_validation.py](11_validation.py) | Reject poison queue payloads BEFORE downloading any blobs |
| 12 | [12_path_safety.py](12_path_safety.py) | Defend filename interpolation against bidi-overrides + path traversal |
| 13 | [13_security_compare.py](13_security_compare.py) | Compare API keys / tokens in constant time |
| 14 | [14_retry.py](14_retry.py) | Wrap Azure/AI calls with tenacity + counter conventions baked in |
| 15 | [15_ingress_classifier.py](15_ingress_classifier.py) | Run the four-gate (extension → MIME → size → magic-byte) ingress pipeline |
| 16 | [16_zip_bomb_defense.py](16_zip_bomb_defense.py) | Reject archives that claim too many entries or too much uncompressed size |
| 17 | [17_ratelimit.py](17_ratelimit.py) | Add per-endpoint token-bucket rate limiting to a FastAPI app |
| 18 | [18_notify.py](18_notify.py) | Build sender-vs-dev email bodies without leaking forensics to senders |
| 19 | [19_subscription.py](19_subscription.py) | Renew Graph webhook subscriptions in a SIGTERM-responsive loop |
| 20 | [20_pdf_sanitize.py](20_pdf_sanitize.py) | Strip JavaScript / OpenAction / annotations from untrusted PDFs |
| 21 | [21_consumer_wrapper.py](21_consumer_wrapper.py) | Dispatch Service Bus messages with dead-letter-vs-abandon classification |
| 22 | [22_identity.py](22_identity.py) | Pick the right Azure credential without hardcoding `DefaultAzureCredential()` |
| 23 | [23_audit_logs.py](23_audit_logs.py) | Emit audit lines with masking + truncation + ISO-8601 timestamps |
| 24 | [24_failclose.py](24_failclose.py) | Codify "fail-closed for auth, fail-open for features" env reads |
| 25 | [25_webhook_route.py](25_webhook_route.py) | Wire a Graph-style webhook with validation handshake + dedup + rate limit |
| 26 | [26_sb_lock.py](26_sb_lock.py) | Hold Service Bus message locks across long-running handlers |
| 27 | [27_alerts_dispatcher.py](27_alerts_dispatcher.py) | Send WARN / ERROR / CRITICAL alerts with dedup + rate-limit + escalation |
| 28 | [28_global_exception_hooks.py](28_global_exception_hooks.py) | Page on-call for uncaught sync + asyncio exceptions |
| 29 | [29_health_probes.py](29_health_probes.py) | Implement `/health/live` + `/health/ready` for Kubernetes |
| 30 | [30_fastapi_middleware.py](30_fastapi_middleware.py) | Time every request, suppress probe noise, alert on 5xx |
| 31 | [31_heartbeat_watchdog.py](31_heartbeat_watchdog.py) | Watchdog a stuck consumer; emit pulse logs on a heartbeat |
| 32 | [32_config_refresh.py](32_config_refresh.py) | Flip `LOG_LEVEL` in App Config and see it apply in 60s — no redeploy |
| 33 | [33_dlq_digest.py](33_dlq_digest.py) | Send a daily DLQ digest with embedded pending-alerts summary |
| 34 | [34_dlq_resubmit_tokens.py](34_dlq_resubmit_tokens.py) | Issue HMAC-signed action tokens for DLQ resubmit links |
| 35 | [35_openai_tracker.py](35_openai_tracker.py) | Track AI cost + tokens across sliding windows; alert on threshold breach |
| 36 | [36_scheduler.py](36_scheduler.py) | Parse 5- or 6-field NCRONTAB into an APScheduler CronTrigger |
| 37 | [37_metrics_endpoint.py](37_metrics_endpoint.py) | Expose latency + counters + AI usage at `/api/metrics` |

## By tier

| Tier 1 (always on, stdlib only) | Tier 2 (opt-in) | Tier 3 (advanced opt-in) |
| --- | --- | --- |
| 01, 02, 03, 04, 05, 06, 07 | 17, 27, 28, 29, 30, 31, 32 | 20, 21, 25, 26, 33, 34, 35, 36, 37 |
| 08, 09, 10, 11, 12, 13 | 14, 15, 16, 18, 19 |  |
| 22, 23, 24 |  |  |

### pip extras each example expects

| Example | Required extra |
| --- | --- |
| 14_retry | `pip install azure-bootstrap[retry]` (pulls `tenacity`) |
| 17_ratelimit, 25_webhook_route, 30_fastapi_middleware, 37_metrics_endpoint, 29_health_probes (only the FastAPI demo bits) | `pip install azure-bootstrap[fastapi]` |
| 20_pdf_sanitize | `pip install azure-bootstrap[pdf-safety]` (pulls `pypdf`) |
| 32_config_refresh, 36_scheduler | `pip install azure-bootstrap[scheduler]` (pulls `apscheduler`) |
| 22_identity | `azure-identity` (already in core deps) |
| Everything else | base install only |

## End-to-end app templates

These three files compose the numbered examples into runnable app
skeletons. Copy one into your project as a starting point.

- [e2e_azure_function.py](e2e_azure_function.py) — v2 successor to the
  v1 [function_app_example.py](function_app_example.py). Shows the
  recommended lazy `_ensure_bootstrap()` pattern, `correlation_scope`
  per request, `@traced` on the handler, audit logging.
- [e2e_fastapi_pipeline.py](e2e_fastapi_pipeline.py) — full FastAPI
  app with `install_middleware`, `install_graph_webhook_route` for
  Microsoft Graph notifications, three health probes, rate-limited
  admin endpoints, `/api/metrics`.
- [e2e_aks_sb_worker.py](e2e_aks_sb_worker.py) — AKS pod main loop
  that pulls Service Bus messages, wraps each in `lock_for_process`
  and `handle_message`, runs heartbeat + consumer watchdog as daemon
  threads, exits cleanly on SIGTERM.

## Contributing

When you add a new module to `azure_bootstrap/`, add a numbered example
file here and a row in the **Reading order** table. The verification
script (see the project's plan file) checks that every numbered file
is referenced in the README and vice versa.
