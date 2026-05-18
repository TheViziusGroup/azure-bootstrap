"""Workload Identity / DefaultAzureCredential wrapper.

Single source of truth for "which Azure credential should this process
use." Replaces ad-hoc ``DefaultAzureCredential()`` instantiation across an
app and codifies the WorkloadIdentity-first preference (no client secrets
in pod env in production).
"""

from __future__ import annotations

import logging
import os
import time
from enum import Enum
from typing import Any

from azure_bootstrap.counters import bump_counter
from azure_bootstrap.tracing.decorators import traced

_logger = logging.getLogger(__name__)

AZURE_TOKEN_AUDIENCE = "api://AzureADTokenExchange"
_DEFAULT_TOKEN_FILE = "/var/run/secrets/azure/tokens/azure-identity-token"


class CredentialKind(str, Enum):
    WORKLOAD_IDENTITY = "workload_identity"
    CLIENT_SECRET = "client_secret"
    DEFAULT = "default"


def credential_kind(
    *,
    tenant_id: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> CredentialKind:
    """Inspect inputs + env to decide which kind ``build_credential`` would return.

    Does not actually construct a credential — useful for /api/health probes.
    """
    tenant = tenant_id or os.environ.get("AZURE_TENANT_ID", "").strip()
    client = client_id or os.environ.get("AZURE_CLIENT_ID", "").strip()
    secret = client_secret or os.environ.get("AZURE_CLIENT_SECRET", "")
    if secret:
        return CredentialKind.CLIENT_SECRET
    if tenant and client:
        return CredentialKind.WORKLOAD_IDENTITY
    return CredentialKind.DEFAULT


def build_credential(
    *,
    tenant_id: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    prefer: CredentialKind | None = None,
    token_file_path: str = _DEFAULT_TOKEN_FILE,
) -> Any:
    """Build the preferred Azure credential for the current environment.

    Resolution order (when ``prefer`` is None):
    1. ``ClientSecretCredential`` when ``client_secret`` (or env) is set.
    2. ``WorkloadIdentityCredential`` when ``tenant_id`` and ``client_id``
       are set but secret is empty.
    3. ``DefaultAzureCredential`` as last-resort fallback.
    """
    try:
        from azure.identity import (  # type: ignore[import-not-found]
            ClientSecretCredential,
            DefaultAzureCredential,
            WorkloadIdentityCredential,
        )
    except ImportError as exc:  # pragma: no cover
        raise ImportError("build_credential requires azure-identity (in core deps)") from exc

    tenant = tenant_id or os.environ.get("AZURE_TENANT_ID", "").strip() or None
    client = client_id or os.environ.get("AZURE_CLIENT_ID", "").strip() or None
    secret = (
        client_secret if client_secret is not None else os.environ.get("AZURE_CLIENT_SECRET", "")
    )

    kind: CredentialKind
    if prefer is CredentialKind.CLIENT_SECRET or (prefer is None and secret):
        if not (tenant and client and secret):
            raise ValueError(
                "ClientSecretCredential requires tenant_id, client_id, and client_secret"
            )
        cred: Any = ClientSecretCredential(tenant, client, secret)
        kind = CredentialKind.CLIENT_SECRET
    elif prefer is CredentialKind.WORKLOAD_IDENTITY or (prefer is None and tenant and client):
        cred = WorkloadIdentityCredential(
            tenant_id=tenant,
            client_id=client,
            token_file_path=token_file_path,
        )
        kind = CredentialKind.WORKLOAD_IDENTITY
    else:
        cred = DefaultAzureCredential()
        kind = CredentialKind.DEFAULT

    _logger.info(
        "Credential built",
        extra={
            "operation": "identity.build_credential",
            "kind": kind.value,
            "tenant_id": tenant or "(unset)",
            "client_id": client or "(unset)",
            "client_secret_present": bool(secret),
        },
    )
    bump_counter(f"identity.credential_built.{kind.value}")
    return cred


def _mock_enabled() -> bool:
    return os.environ.get("USE_MOCK_BOOTSTRAP", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@traced(operation="identity.credential_health", alert_on_error="warn")
def credential_health(
    scopes: tuple[str, ...] = ("https://management.azure.com/.default",),
) -> dict[str, Any]:
    """Acquire a token, measure latency, return a health-check dict."""
    if _mock_enabled():
        return {"status": "ok", "mock": True}

    kind = credential_kind()
    try:
        cred = build_credential()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "kind": kind.value, "message": str(exc)[:200]}

    start = time.monotonic()
    try:
        token = cred.get_token(*scopes)
        latency_ms = int((time.monotonic() - start) * 1000)
        scope_short = scopes[0].rsplit("/", 1)[-1] if scopes else "unknown"
        bump_counter(f"identity.token_acquired.{scope_short}")
        return {
            "status": "ok",
            "kind": kind.value,
            "latency_ms": latency_ms,
            "expires_on": getattr(token, "expires_on", None),
        }
    except Exception as exc:  # noqa: BLE001
        bump_counter("identity.token_failed")
        return {
            "status": "error",
            "kind": kind.value,
            "message": str(exc)[:200],
        }


__all__ = [
    "AZURE_TOKEN_AUDIENCE",
    "CredentialKind",
    "build_credential",
    "credential_health",
    "credential_kind",
]
