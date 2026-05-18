# Changelog

All notable changes to the Azure Bootstrap library.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-05-18

Major expansion: bakes in the cross-cutting logging, observability, alerting,
and Azure-integration primitives that every project was re-implementing on
top of v1. **No v1 imports change.** All new functionality is additive and
gated behind optional extras where it has runtime dependencies.

### Added

#### Tier 1 — always-on (stdlib-only)

- `azure_bootstrap.logging` — `configure_logging()` (idempotent),
  `ExtraFieldsFormatter` (key=repr pairs, two-space gap, filters reserved +
  underscore-prefixed keys), `LoggingExtraConflictError`, `CorrelationFilter`,
  `correlation_scope()` context manager with arbitrary kwargs, `mask_api_key`,
  `mask_bearer_token`, `mask_email_address`, `mask_secrets_in_dict`,
  `sanitize_for_log` (strips control chars 0x00–0x1f, 0x7f), `content_preview`,
  `safe_json_dumps`, `_safe_repr` (primitive-only, never invokes arbitrary
  `__repr__`), `silence_noisy_loggers` with sensible defaults (`pdfminer`,
  Azure SDK chatty paths, `urllib3`, etc.), `debug_logging_enabled`,
  `effective_log_level`, `env_flag`, `register_secret_keys`,
  `register_noisy_logger`.
- `azure_bootstrap.tracing` — `@traced` decorator (auto-detects async, records
  latency on success + error, lazy alert dispatch, sensitive-arg masking,
  slow-budget alerts), `@traced_async` (alias), `timed_operation` context
  manager, `log_exception_context`, `latency_snapshot` with p50/p95/p99/max
  per operation, `register_slow_threshold`, `default_slow_threshold`.
- `azure_bootstrap.counters` — thread-safe `bump_counter`, `counter_snapshot`.
- `azure_bootstrap.bootstrap` — `ensure_bootstrap` (lazy idempotent wrapper
  around v1 `initialize_application`), `bootstrap_initialized`,
  `load_local_settings` (Azure-Functions-style JSON loader, never overrides
  existing env).
- Top-level — `refresh_setting(*names)` (net-new v2 function — re-reads
  named keys from the cached App Configuration repo).

#### Tier 2 — opt-in

- `azure_bootstrap.alerts` (extra: `alerts`) — `AlertSeverity`,
  `alert_dev_team` (tiered: WARN log-only, ERROR digest + escalation,
  CRITICAL email), `register_dispatcher` (caller supplies any
  `send(recipients, subject, html)` callable), dedup (default 10-min window),
  rate-limit (default 30/hour, folds overflow into digest),
  escalation ladder (5 ERRORs in 15m → CRITICAL), `drain_pending_alerts`,
  `render_pending_alerts_html`, `install_global_exception_hooks` (chains
  previous `sys.excepthook` + asyncio handler), `reset_state` (test-only).
- `azure_bootstrap.health` (extra: `health`) — `check_app_config_health`,
  `check_app_insights_health`, `check_app_insights_logging` (walks every
  handler to detect an attached Azure Monitor handler).
- `azure_bootstrap.fastapi_middleware` (extra: `fastapi`) —
  `install_middleware(app, …)` for FastAPI: probes silent, non-probes log +
  alert on 5xx/uncaught.
- `azure_bootstrap.heartbeat` (extra: `heartbeat`) — `start_heartbeat`,
  `start_consumer_watchdog` (1-hour resilence cooldown longer than alerts
  dedup), `record_consumer_iteration`, `record_message_settled`,
  `start_background_monitors`.
- `azure_bootstrap.config_refresh` (extra: `config-refresh`) —
  `refresh_log_flags` for APScheduler `CronTrigger(minute='*')`.

#### Tier 3 — advanced opt-in

- `azure_bootstrap.tokens` (extra: `tokens`) — `issue_action_token`,
  `verify_action_token`, `InvalidActionToken`. HMAC-SHA256 +
  `hmac.compare_digest`, sorted-keys JSON, base64url-no-pad.
- `azure_bootstrap.servicebus` (extra: `servicebus`) — `check_dlq_growth_rate`
  (CRITICAL on excessive growth), `run_dlq_digest` (daily digest email with
  optional resubmit link + pending-alerts summary), `build_dlq_digest_body`,
  `issue_resubmit_token`, `verify_resubmit_token`, `InvalidResubmitToken`,
  re-exports for consumer watchdog primitives.
- `azure_bootstrap.openai` (extra: `openai`) — `record_usage`, `acquire`
  (soft TPM cap; never blocks longer than `AI_RATE_LIMIT_MAX_WAIT_SECONDS`),
  `record_rate_limit_event`, `usage_snapshot` with sliding windows (60s, 60m,
  24h), `check_thresholds_and_alert` (30-min per-key cooldown),
  `register_pricing`, `AiUsageTracker`. Default pricing includes GPT-4o
  family, o1, GPT-5-mini AND Claude 3.5 Sonnet/Haiku, Claude 3 Opus/Haiku.
  Per-deployment env overrides via `AI_PRICING_<NORMALIZED>_INPUT_PER_1K` /
  `_OUTPUT_PER_1K`.
- `azure_bootstrap.scheduler` (extra: `scheduler`) — `parse_cron_trigger`
  (5- and 6-field NCRONTAB → APScheduler CronTrigger, fallback to `*/15`).
- `azure_bootstrap.metrics` (extra: `metrics`) — `build_metrics_snapshot`
  for `/api/metrics` endpoints, soft-imports each contributor.

### Changed

- `__version__` bumped to `2.0.0`.
- `azure_bootstrap/services/application_bootstrap.py:initialize_application`
  now caches the returned repo via `get_last_initialized_repo()` so the new
  `refresh_setting` can re-read keys without re-running bootstrap. The
  function signature and return type are unchanged.
- Coverage threshold raised from 80 % → 85 % for new code.
- Optional dependencies: new keys `alerts`, `health`, `fastapi`, `heartbeat`,
  `config-refresh`, `servicebus`, `openai`, `tokens`, `scheduler`, `metrics`,
  `all` under `[project.optional-dependencies]`.

### Added (Part 2 — error handling & defensive coding)

#### Tier 1 — always-on (stdlib-only)

- `azure_bootstrap.exceptions` — project-neutral exception hierarchy:
  `PipelineError`, `UnrecoverableError` (marker; subclasses
  `InvalidMessageError`, `OversizedAttachmentError`,
  `MalformedAttachmentError`, `ZipBombError`, `UpstreamResourceMissing`),
  `TransientError` (marker; subclasses `RateLimitError`, `NetworkError`,
  `AuthenticationError`). `is_unrecoverable(exc)` classifier;
  `register_unrecoverable(*types)` for SDK exceptions outside the tree.
- `azure_bootstrap.softfail` — `soft_fail_with(...)`, `soft_fail(...)`
  context manager, `SoftFailResult`. Both re-raise unrecoverable exceptions
  by default (set `re_raise_unrecoverable=False` to opt out).
- `azure_bootstrap.phases` — `run_phase(...)`, `run_phases(...)`,
  `PhaseResult`. `run_phase` NEVER re-raises; per-phase counter convention
  `{namespace}.{name}.{ok|failed|<aggregate>}`.
- `azure_bootstrap.validation` — `validate_message`, `MessageSchema`,
  `FieldRule`, `queue_message_schema(...)` helper. Default path-field
  rules reject `..` and `://` substrings.
- `azure_bootstrap.path_safety` — `sanitize_path_segment(...)` (strips
  bidi/zero-width chars first), `confine_to_root(raw, allowed_root)`.
- `azure_bootstrap.security` — `compare_secrets(a, b)`,
  `verify_api_key_header(...)` async FastAPI helper.

#### Tier 2 — opt-in

- `azure_bootstrap.retry` (extra: `retry`) — `build_retry(...)`,
  `retry_azure_transient(...)`, `retry_ai_transient(...)`. Counter
  conventions: `{ns}.runs`, `{ns}.calls.ok`, `{ns}.calls.invalid_response`,
  `{ns}.calls.rate_limit_or_http_error`, `{ns}.calls.unexpected_error`.
- `azure_bootstrap.ingress` (extra: `ingress`) — `AttachmentClassifier`,
  `ExtensionAllowlist`, `MimeAllowlist`, `classify_bytes`,
  `enforce_size_cap`, `enforce_zip_safety_limits`. Fixed gate order:
  extension → MIME → size → magic-byte. Counter conventions:
  `attachment.rejected.{gate}`, `attachment.classified.{kind}`,
  `attachment.mismatched_extension`.
- `azure_bootstrap.ratelimit` (extra: `ratelimit`) — `TokenBucket`,
  `fastapi_rate_limit`, `webhook_bucket`, `admin_bucket` presets.
  Atomic refill+check+consume; 429 response body empty by default.
- `azure_bootstrap.notify` (extra: `notify`) — `should_notify_sender`
  per-sender throttle; `build_failure_alert_body`,
  `build_validation_notice_body`, `build_unprocessable_notification`
  two-tier email body builders. Sender bodies abuse-safe (no correlation
  IDs / tracebacks / blob paths leaked to the sender side).
- `azure_bootstrap.subscription` (extra: `subscription`) —
  `RenewableResource`, `SubscriptionGone`, `ensure_resource`,
  `renewal_loop`. Renewal loop sleeps in ≤ 5 s slices for SIGTERM
  responsiveness.

#### Tier 3 — advanced opt-in

- `azure_bootstrap.pdf_safety` (extra: `pdf-safety`) —
  `sanitize_pdf_for_passthrough(reader)` strips catalog OpenAction,
  /AA, /JavaScript, /Names, /URI; per-page /AA + /OpenAction;
  per-annotation /A + /AA; AcroForm-field /A + /AA. Best-effort
  (returns the reader unchanged on any exception).
- `azure_bootstrap.servicebus.consumer_wrapper` (existing `servicebus`
  extra) — `handle_message(receiver, msg, processor, ...)` end-to-end
  consumer with schema validation, correlation scope, dead-letter vs
  abandon routing via `is_unrecoverable`, best-effort `notify_failure`
  before dead-letter, `record_message_settled()` in `finally`.

### Added (Part 3 — security, identity, audit)

#### Tier 1 — always-on

- `azure_bootstrap.identity` — `build_credential(...)` prefers
  `WorkloadIdentityCredential` over `ClientSecretCredential` over
  `DefaultAzureCredential`. `credential_kind()` probe; `credential_health()`
  acquires a token and reports latency. Never logs the client secret.
- `azure_bootstrap.audit` — `build_audit_extra(operation, **fields)`
  masks email-shaped values via `mask_email_address`, other secret-named
  fields via `mask_api_key`; truncates subject/error/traceback/etc. via
  `sanitize_for_log`; always inserts UTC ISO-8601 `timestamp`.
- `azure_bootstrap.failclose` — `require_env(name)`, `optional_env(name)`,
  `fail_open_env(name)`. `ConfigurationError` re-exported from
  `azure_bootstrap.models.exceptions` (single canonical class; v1 callers
  unchanged).

#### Tier 2 — opt-in

- `azure_bootstrap.auth` (extra: `auth`) — `WebhookDedup`,
  `verify_webhook_client_state`, `validation_token_handshake`,
  `install_graph_webhook_route(app, path, ...)` FastAPI route installer.
  Pipeline: validation token → rate limit → JSON parse → per-entry
  clientState → dedup → background dispatch → 202 Accepted. 401/429
  responses omit body.
- `azure_bootstrap.sb_lock` (extra: `sb-lock`) — `lock_for_process`
  context manager + `ManagedLock` OO variant. Default
  `max_lock_renewal_seconds=3600`. Swallows AutoLockRenewer construction
  failure (defense, not correctness).

### Skipped (per user scope decision)

Three Part-3 modules were explicitly cut as too niche / unusual for a
Python library:

- `azure_bootstrap.parity/` (Helm chart App-Config-vs-Key-Vault parity
  check)
- `azure_bootstrap.github_oidc/` (federated-credential setup + CLI)
- `azure_bootstrap.manifests/` (bundled Helm-templated K8s YAMLs)

Apps that need these can lift the reference snippets from the spec into
their own deploy tooling.

### Documentation

- New flat examples library under [examples/](examples/) — 37 numbered
  single-concept files (`01_quickstart.py` … `37_metrics_endpoint.py`)
  plus three end-to-end app templates (`e2e_azure_function.py`,
  `e2e_fastapi_pipeline.py`, `e2e_aks_sb_worker.py`). Every example is
  runnable with `USE_MOCK_BOOTSTRAP=true` (no real Azure required) and
  ends with an `# ── Expected output ──` block. See
  [examples/README.md](examples/README.md) for the reading order +
  per-example pip-extra requirements.
- New [MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md) with the v1 → v2
  upgrade path + extras matrix.
- [README.md](README.md), [CLAUDE.md](CLAUDE.md),
  [CONTRIBUTING.md](CONTRIBUTING.md) refreshed for the v2 surface
  (extras matrix, repository structure, coverage thresholds, version
  references).

### Preserved (v1 contract, byte-identical)

Every entry in v1's `__all__` is still exported from the top-level package
and behaves exactly as before:

`initialize_application`, `get_bootstrap_logger`,
`create_enhanced_config_repository`, `ensure_bootstrap_logging`,
`telemetry_manager`, `ApplicationBootstrap`, `BootstrapLogger`,
`ExtraFieldsFormatter` (the v1 JSON-with-pipe one — the new v2 formatter
lives at `azure_bootstrap.logging.formatter.ExtraFieldsFormatter`),
`TelemetryManager`, `EnhancedConfigRepository`, `SecretsRepository`,
`ApplicationBootstrapInterface`, `BootstrapLoggerInterface`,
`TelemetryManagerInterface`, `EnhancedConfigRepositoryInterface`,
`SecretsRepositoryInterface`, `RepositoryError`, `ConfigurationError`,
`KeyVaultError`, `__version__`.

See [MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md) for the opt-in upgrade path.

---

## [1.0.0] — 2026-04-09

Initial public release. See [CLAUDE.md](CLAUDE.md) § Version History for
details.
