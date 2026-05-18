"""Audit log conventions.

Standardize the audit-line pattern so PII/secret leakage at log call sites
is handled consistently. Mask email-shaped values via the v2
:func:`mask_email_address` helper; non-email secrets via :func:`mask_api_key`;
truncate / strip control chars from text fields via :func:`sanitize_for_log`.

Always inserts a UTC ISO-8601 timestamp and the operation name into the
extras dict so structured aggregators have a stable schema.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Any

from azure_bootstrap.counters import bump_counter
from azure_bootstrap.logging.masking import (
    mask_api_key,
    mask_email_address,
    sanitize_for_log,
)

AUDIT_LINE_NAMES: tuple[str, ...] = (
    "EMAIL_AUDIT",
    "REPORT_AUDIT",
    "SHAREPOINT_AUDIT",
    "BLOB_AUDIT",
    "QUEUE_AUDIT",
    "AUTH_AUDIT",
)

AUDIT_MASKED_FIELDS: frozenset[str] = frozenset(
    {
        "sender",
        "recipient",
        "to",
        "from",
        "email",
        "api_key",
        "token",
        "secret",
        "client_secret",
        "connection_string",
    }
)

AUDIT_TRUNCATED_FIELDS: dict[str, int] = {
    "subject": 100,
    "error": 500,
    "exception_message": 500,
    "error_summary": 500,
    "traceback": 2000,
    "body_preview": 500,
    "filename": 256,
}


def mask_email_field(value: str | None) -> str:
    """Ergonomic alias of :func:`mask_email_address`."""
    return mask_email_address(value)


def truncate_field(name: str, value: Any) -> Any:
    """Apply ``AUDIT_TRUNCATED_FIELDS`` truncation when applicable."""
    cap = AUDIT_TRUNCATED_FIELDS.get(name.lower())
    if cap is None or not isinstance(value, str):
        return value
    return sanitize_for_log(value, max_len=cap)


def _is_email_shaped(value: Any) -> bool:
    return isinstance(value, str) and "@" in value


def build_audit_extra(operation: str, **fields: Any) -> dict[str, Any]:
    """Construct the ``extra={}`` dict for an audit log call.

    Email-shaped values for masked fields go through :func:`mask_email_address`;
    other masked values through :func:`mask_api_key`. Truncated fields get
    :func:`sanitize_for_log` applied with the configured cap.

    Always adds ``operation`` and a UTC ISO-8601 ``timestamp``.
    """
    out: dict[str, Any] = {
        "operation": operation,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    for name, value in fields.items():
        lowered = name.lower()
        if lowered in AUDIT_MASKED_FIELDS:
            if value:
                if _is_email_shaped(value):
                    out[name] = mask_email_address(value)
                else:
                    out[name] = mask_api_key(value if isinstance(value, str) else str(value))
                bump_counter(f"audit.field_masked.{lowered}")
            else:
                out[name] = value
            continue
        if lowered in AUDIT_TRUNCATED_FIELDS and isinstance(value, str):
            truncated = sanitize_for_log(value, max_len=AUDIT_TRUNCATED_FIELDS[lowered])
            if truncated != value:
                bump_counter(f"audit.field_truncated.{lowered}")
            out[name] = truncated
            continue
        out[name] = value
    return out


__all__ = [
    "AUDIT_LINE_NAMES",
    "AUDIT_MASKED_FIELDS",
    "AUDIT_TRUNCATED_FIELDS",
    "build_audit_extra",
    "mask_email_field",
    "truncate_field",
]
