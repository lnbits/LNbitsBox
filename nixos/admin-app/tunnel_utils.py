from __future__ import annotations

import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def generate_client_id(length: int = 12) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alphabet[secrets.randbelow(len(alphabet))] for _ in range(length))


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def select_canonical_tunnel(tunnels: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Choose canonical tunnel from lnpro tunnel list:
    - Prefer active tunnel with latest expiry.
    - Otherwise pick latest expiry overall.
    """
    if not tunnels:
        return None

    def key(item: dict[str, Any]) -> tuple[int, float]:
        expires = _parse_dt(item.get("expires_at"))
        stamp = expires.timestamp() if expires else 0.0
        is_active = 1 if str(item.get("status", "")).lower() == "active" else 0
        return is_active, stamp

    active = [t for t in tunnels if str(t.get("status", "")).lower() == "active"]
    if active:
        return max(active, key=key)
    return max(tunnels, key=key)


def choose_invoice_action(current_tunnel: dict[str, Any] | None) -> str:
    return "renew" if current_tunnel and current_tunnel.get("tunnel_id") else "create"


def is_pending_invoice_paid(
    pending: dict[str, Any] | None,
    canonical_tunnel: dict[str, Any] | None,
) -> bool:
    if not pending or not canonical_tunnel:
        return False

    pending_tunnel_id = pending.get("tunnel_id")
    canonical_id = canonical_tunnel.get("tunnel_id")
    if not pending_tunnel_id or pending_tunnel_id != canonical_id:
        return False

    action = pending.get("action")
    if action == "create":
        return str(canonical_tunnel.get("status", "")).lower() == "active"

    if action == "renew":
        before = _parse_dt(pending.get("baseline_expires_at"))
        after = _parse_dt(canonical_tunnel.get("expires_at"))
        if not before or not after:
            return False
        return after > before

    return False


def write_secure_json(path: Path, data: dict[str, Any], mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(data, tmp, indent=2, sort_keys=True)
        tmp.flush()
        os.fchmod(tmp.fileno(), mode)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    os.chmod(path, mode)


def read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)


def build_connect_script(ssh_private_key: str, tunnel: dict[str, Any], local_port: int = 5000) -> str:
    remote_port = int(tunnel.get("remote_port", 0))
    ssh_user = tunnel.get("ssh_user", "ubuntu")
    ssh_host = tunnel.get("ssh_host", "lnpro.xyz")
    return (
        "cat > reverse-proxy-key <<'EOF'\n"
        f"{ssh_private_key.rstrip()}\n"
        "EOF\n"
        "chmod 600 reverse-proxy-key\n"
        f"ssh -i ./reverse-proxy-key -N -R {remote_port}:localhost:{local_port} {ssh_user}@{ssh_host}"
    )
