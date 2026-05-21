"""Sumo Logic logging transport — buffered, background-thread HTTP shipper.

``SumoLogicHandler`` is a ``logging.Handler`` that batches formatted records and
POSTs them to a Sumo Logic `HTTP Source
<https://help.sumologic.com/docs/send-data/hosted-collectors/http-source/logs-metrics/>`_
collector endpoint as newline-delimited JSON.

Design guarantees:
- **Never blocks** the calling thread — ``emit()`` only appends to an in-memory
  buffer; a daemon thread does the network I/O.
- **Never raises** — every public method is wrapped; failures bump a counter and
  route through ``handleError``.
- **Bounded** — a ``deque(maxlen=...)`` drops oldest records under sustained
  backpressure rather than growing without limit.
- **Flushes** on a timer, when the buffer crosses ``batch_size``, and at process
  exit via ``atexit``.

Wire behavior follows Sumo Logic's documented contract for HTTP Sources:
- Batched **NDJSON** (one JSON object per line, all lines in a single POST so
  Sumo's per-request multiline grouping works).
- **gzip** compression for bodies at/above ``gzip_threshold`` (``Content-Encoding:
  gzip``); Sumo strongly recommends compression.
- **Byte-size-aware batching** capped at ``max_batch_bytes`` (Sumo's documented
  payload sweet spot is 100 KB–1 MB per POST).
- **Status-aware retry** via ``urllib3``'s ``Retry`` mounted on a
  ``requests.Session``: retries 408/429/5xx with exponential backoff + jitter,
  **honors ``Retry-After``** (critical for 429, which Sumo drops unless resent),
  and does **not** retry 401/other 4xx (an unrecoverable bad URL/token).
- Optional **auth-header mode** (``x-sumo-token``) and per-request
  **``X-Sumo-Fields``** metadata.

``requests`` (and its vendored ``urllib3``) is imported **lazily** inside the
handler so ``import azure_bootstrap`` never requires the optional ``[sumologic]``
extra; ``make_sumo_logic_handler()`` returns ``None`` (transport stays a soft
no-op) when ``requests`` is not installed.
"""

from __future__ import annotations

import atexit
import gzip
import logging
import threading
from collections import deque
from collections.abc import Mapping
from typing import Any

from azure_bootstrap.counters import bump_counter
from azure_bootstrap.failclose import fail_open_env, optional_env
from azure_bootstrap.logging.correlation import CorrelationFilter
from azure_bootstrap.logging.jsonformatter import JsonLogFormatter

_COUNTER_POSTS = "sumologic.transport.posts"
_COUNTER_OK = "sumologic.transport.ok"
_COUNTER_ERROR = "sumologic.transport.error"
_COUNTER_THROTTLED = "sumologic.transport.throttled"
_COUNTER_DROPPED = "sumologic.transport.dropped"
_COUNTER_RECORDS = "sumologic.transport.records"


class SumoLogicHandler(logging.Handler):
    """Buffered handler that ships log lines to a Sumo Logic HTTP Source."""

    def __init__(
        self,
        *,
        endpoint_url: str,
        source_category: str | None = None,
        source_host: str | None = None,
        source_name: str = "azure-bootstrap",
        source_token: str | None = None,
        fields: Mapping[str, str] | None = None,
        batch_size: int = 100,
        max_batch_bytes: int = 1_000_000,
        gzip_threshold: int = 1024,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
        timeout: float = 5.0,
    ) -> None:
        super().__init__()
        self.endpoint_url = endpoint_url
        self.source_category = source_category
        self.source_host = source_host
        self.source_name = source_name
        self.source_token = source_token
        self.fields = dict(fields) if fields else {}
        self.batch_size = max(1, batch_size)
        self.max_batch_bytes = max(1, max_batch_bytes)
        self.gzip_threshold = max(0, gzip_threshold)
        self.flush_interval = max(0.1, flush_interval)
        self.timeout = timeout

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())

        # Lazy import — keeps `import azure_bootstrap` working without the
        # [sumologic] extra. Raises ImportError here if requests is absent;
        # make_sumo_logic_handler() turns that into a soft no-op (returns None).
        self._session: Any = _build_session()

        self._buffer: deque[str] = deque(maxlen=max(1, max_buffer))
        self._buffer_lock = threading.Lock()
        self._flush_now = threading.Event()
        self._stop = threading.Event()
        self._closed = False
        self._close_lock = threading.Lock()

        self._thread = threading.Thread(target=self._run, name="sumologic-transport", daemon=True)
        self._thread.start()

        # Stored so close() can unregister and avoid duplicate-close in tests.
        self._atexit_handle = self.close
        atexit.register(self._atexit_handle)

    # ── logging.Handler API ────────────────────────────────────────────
    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
            maxlen = self._buffer.maxlen or 0
            with self._buffer_lock:
                was_full = maxlen > 0 and len(self._buffer) >= maxlen
                self._buffer.append(line)
                size = len(self._buffer)
            if was_full:
                bump_counter(_COUNTER_DROPPED)
            if size >= self.batch_size:
                self._flush_now.set()
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        try:
            self._drain_and_post()
        except Exception:
            pass

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
        try:
            self._stop.set()
            self._flush_now.set()
            if self._thread.is_alive() and self._thread is not threading.current_thread():
                self._thread.join(timeout=max(self.timeout, self.flush_interval) + 1.0)
            # Final synchronous drain for anything left buffered.
            self._drain_and_post()
        except Exception:
            pass
        finally:
            try:
                self._session.close()
            except Exception:
                pass
            try:
                atexit.unregister(self._atexit_handle)
            except Exception:
                pass
            super().close()

    # ── background loop ────────────────────────────────────────────────
    def _run(self) -> None:
        while not self._stop.is_set():
            self._flush_now.wait(self.flush_interval)
            self._flush_now.clear()
            try:
                self._drain_and_post()
            except Exception:
                pass

    def _drain_and_post(self) -> None:
        while True:
            with self._buffer_lock:
                if not self._buffer:
                    return
                # Accumulate up to batch_size records OR ~max_batch_bytes,
                # whichever comes first, so a POST stays near Sumo's sweet spot.
                batch: list[str] = []
                nbytes = 0
                while self._buffer and len(batch) < self.batch_size:
                    line = self._buffer[0]
                    # +1 for the newline joiner; always take at least one line.
                    line_bytes = len(line.encode("utf-8")) + 1
                    if batch and nbytes + line_bytes > self.max_batch_bytes:
                        break
                    self._buffer.popleft()
                    batch.append(line)
                    nbytes += line_bytes
            self._post_batch(batch)

    def _post_batch(self, lines: list[str]) -> None:
        if not lines:
            return
        body = "\n".join(lines).encode("utf-8")
        headers = {"Content-Type": "application/json", "X-Sumo-Name": self.source_name}
        if self.source_category:
            headers["X-Sumo-Category"] = self.source_category
        if self.source_host:
            headers["X-Sumo-Host"] = self.source_host
        if self.source_token:
            headers["x-sumo-token"] = self.source_token
        if self.fields:
            # Must be enabled in the org's Fields schema or Sumo silently drops it.
            headers["X-Sumo-Fields"] = ",".join(f"{k}={v}" for k, v in self.fields.items())
        if len(body) >= self.gzip_threshold:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"

        bump_counter(_COUNTER_POSTS)
        try:
            # The session's mounted Retry adapter handles 408/429/5xx with
            # backoff+jitter and honors Retry-After; 401/other-4xx are not
            # retried. We inspect the final status ourselves (raise_on_status
            # is False) and never re-raise — logging must not crash the caller.
            resp = self._session.post(
                self.endpoint_url, data=body, headers=headers, timeout=self.timeout
            )
        except Exception:
            bump_counter(_COUNTER_ERROR)
            return  # network failure — drop the batch, never block or grow
        status = getattr(resp, "status_code", 0)
        if 200 <= status < 300:
            bump_counter(_COUNTER_OK)
            bump_counter(_COUNTER_RECORDS, len(lines))
            return
        if status == 429:
            bump_counter(_COUNTER_THROTTLED)
        bump_counter(_COUNTER_ERROR)


def _build_session() -> Any:
    """Build a ``requests.Session`` with a status-aware retry adapter.

    Imported lazily so the optional ``requests`` dependency is only required
    when the Sumo Logic transport is actually constructed.
    """
    import requests  # type: ignore[import-untyped]
    from requests.adapters import HTTPAdapter  # type: ignore[import-untyped]
    from urllib3.util.retry import Retry

    retry = Retry(
        total=5,
        backoff_factor=1.0,
        backoff_jitter=0.3,
        status_forcelist=(408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=4)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def make_sumo_logic_handler() -> logging.Handler | None:
    """Build a :class:`SumoLogicHandler` from environment configuration.

    Returns ``None`` (transport stays disabled) when ``SUMO_LOGIC_COLLECTOR_URL``
    is unset — the open default here is intentional: absence of an endpoint means
    "Sumo shipping not configured", which is a safe no-op for a logging sink.

    Also returns ``None`` when the optional ``requests`` dependency (the
    ``[sumologic]`` extra) is not installed, so enabling the transport without
    the extra is a soft no-op rather than an error.
    """
    endpoint = fail_open_env("SUMO_LOGIC_COLLECTOR_URL")
    if not endpoint:
        return None

    try:
        return SumoLogicHandler(
            endpoint_url=endpoint,
            source_category=optional_env("SUMO_LOGIC_SOURCE_CATEGORY") or None,
            source_host=optional_env("SUMO_LOGIC_SOURCE_HOST") or None,
            source_token=optional_env("SUMO_LOGIC_COLLECTOR_TOKEN") or None,
            fields=_parse_fields(optional_env("SUMO_LOGIC_FIELDS")),
            batch_size=_int_env("SUMO_LOGIC_BATCH_SIZE", 100),
            max_batch_bytes=_int_env("SUMO_LOGIC_MAX_BATCH_BYTES", 1_000_000),
            gzip_threshold=_int_env("SUMO_LOGIC_GZIP_THRESHOLD", 1024),
            flush_interval=_float_env("SUMO_LOGIC_FLUSH_INTERVAL", 5.0),
            max_buffer=_int_env("SUMO_LOGIC_MAX_BUFFER", 10_000),
            timeout=_float_env("SUMO_LOGIC_TIMEOUT", 5.0),
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "SUMO_LOGIC_COLLECTOR_URL set but the [sumologic] extra (requests) "
            "is not installed — Sumo Logic transport disabled.",
        )
        return None


def _parse_fields(raw: str | None) -> dict[str, str]:
    """Parse a ``"k=v,k2=v2"`` string into a dict; ignore malformed pairs."""
    if not raw:
        return {}
    out: dict[str, str] = {}
    for pair in raw.split(","):
        key, sep, value = pair.partition("=")
        key = key.strip()
        if sep and key:
            out[key] = value.strip()
    return out


def _int_env(name: str, default: int) -> int:
    raw = optional_env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = optional_env(name)
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


__all__ = ["SumoLogicHandler", "make_sumo_logic_handler"]
