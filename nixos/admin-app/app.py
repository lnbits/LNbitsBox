#!/usr/bin/env python3
"""LNbitsBox Admin Dashboard — system monitoring and service management"""

import json
import io
import os
import shlex
import sys
import tempfile
import time
import grp
import stat
try:
    import crypt
except ModuleNotFoundError:
    crypt = None  # Removed in Python 3.13; only needed on NixOS Pi
import shutil
import subprocess
import threading
import zipfile
from collections import deque
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from mnemonic import Mnemonic
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, send_file
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from tunnel_utils import (
    build_connect_script,
    choose_invoice_action,
    generate_client_id,
    is_pending_invoice_paid,
    read_json,
    select_canonical_tunnel,
    write_secure_json,
)
from recovery_utils import (
    available_restore_components,
    build_backup_manifest,
    compatibility_report,
    file_sha256,
    load_backup_container,
    parse_iso_datetime,
    package_encrypted_backup,
    package_plain_backup,
    read_json_file,
    utc_now_iso,
    validate_manifest_files,
    write_json_file,
)

app = Flask(__name__, static_url_path="/box/static")
app.secret_key = os.urandom(24)
# Trust the single local Caddy proxy in front of the admin app.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
csrf = CSRFProtect(app)

# Configuration
DEV_MODE = os.environ.get("DEV_MODE", "false") == "true"
SSH_USER = "lnbitsadmin"
SPARK_URL = os.environ.get("SPARK_URL", "http://127.0.0.1:8765")
try:
    SPARK_SIDECAR_API_KEY = Path("/var/lib/spark-sidecar/api-key.env").read_text().strip().split("=")[1]
except Exception:
    SPARK_SIDECAR_API_KEY = ""
LNBITS_URL = os.environ.get("LNBITS_URL", "http://127.0.0.1:5000")
ALLOWED_SERVICES = ["lnbits", "spark-sidecar", "tor"]
LNBITS_DB_PATH = Path("/var/lib/lnbits/database.sqlite3")
SPARK_MNEMONIC_FILE = (
    Path("/tmp/lnbitspi-test/spark-sidecar/mnemonic")
    if DEV_MODE else Path("/var/lib/spark-sidecar/mnemonic")
)
UPDATE_STATE_DIR = Path("/var/lib/lnbitsbox-update")
VERSION_FILE = Path("/etc/lnbitsbox-version")
GITHUB_RELEASES_URL = "https://api.github.com/repos/lnbits/LNbitsBox/releases/latest"
TUNNEL_SERVICE_NAME = "lnbitsbox-reverse-tunnel"
TUNNEL_API_BASE_URL = os.environ.get(
    "LNBITSBOX_TUNNEL_API_BASE_URL",
    "https://lnbits.lnpro.xyz/reverse_proxy/api/v1",
).rstrip("/")
TUNNEL_PUBLIC_ID = os.environ.get("LNBITSBOX_TUNNEL_PUBLIC_ID", "aE4CBGPeRqcJufpWDVh53G")
TUNNEL_SSH_USER_FALLBACK = os.environ.get("LNBITSBOX_TUNNEL_SSH_USER", "ubuntu")
TUNNEL_SSH_HOST_FALLBACK = os.environ.get("LNBITSBOX_TUNNEL_SSH_HOST", "lnpro.xyz")
TUNNEL_LOCAL_PORT = int(os.environ.get("LNBITSBOX_TUNNEL_LOCAL_PORT", "5000"))
TUNNEL_STATE_DIR = (
    Path("/tmp/lnbitspi-test/tunnel") if DEV_MODE else Path("/var/lib/lnbitsbox-tunnel")
)
TUNNEL_STATE_FILE = TUNNEL_STATE_DIR / "state.json"
TUNNEL_KEY_FILE = TUNNEL_STATE_DIR / "reverse-proxy-key"
TUNNEL_RUNTIME_ENV = TUNNEL_STATE_DIR / "runtime.env"
WPA_SUPPLICANT_CONF = Path("/etc/wpa_supplicant.conf")
TOR_HOSTNAME_FILE = Path("/var/lib/tor/onion/lnbits/hostname")
RECOVERY_STATE_DIR = Path("/tmp/lnbitspi-test/recovery") if DEV_MODE else Path("/var/lib/lnbitsbox-recovery")
RECOVERY_BACKUP_DIR = RECOVERY_STATE_DIR / "backups"
RECOVERY_STATE_FILE = RECOVERY_STATE_DIR / "state.json"
RECOVERY_SCHEDULE_FILE = RECOVERY_STATE_DIR / "schedule.json"

RECOVERY_DESTINATIONS = {
    "local": {
        "label": "Local recovery storage",
        "path": RECOVERY_BACKUP_DIR,
        "writable": True,
        "reason": "",
        "detail": f"Saved to {RECOVERY_BACKUP_DIR}",
    },
}

# Stats history — 2 hours at 30s intervals = 240 data points
STATS_INTERVAL = 30
STATS_HISTORY_SIZE = 240
stats_history = deque(maxlen=STATS_HISTORY_SIZE)
stats_lock = threading.Lock()

# WiFi connection state
wifi_connect_status = {"status": "idle", "message": "", "ip": ""}
wifi_connect_lock = threading.Lock()

# Tunnel remote sync state
TUNNEL_REMOTE_SYNC_MIN_INTERVAL = 10
_tunnel_remote_sync_lock = threading.Lock()
_tunnel_remote_sync = {
    "in_flight": False,
    "last_started_at": 0.0,
    "last_finished_at": 0.0,
}

RECOVERY_COMPONENT_LABELS = {
    "database": "LNbits database",
    "spark": "Spark wallet seed",
    "config": "Device config",
    "tunnel": "Tunnel config",
    "wifi": "Wi-Fi config",
    "tor": "Tor metadata",
    "update": "Update state",
}


def _json_response(*, data: dict[str, Any] | None = None, status_code: int = 200, **payload):
    body = dict(payload)
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def _json_error(message: str, status_code: int = 500, **payload):
    return _json_response(status="error", message=message, status_code=status_code, **payload)


# ── Tunnel Helpers ──────────────────────────────────────────────────

def _ensure_tunnel_state_dir():
    TUNNEL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(TUNNEL_STATE_DIR, 0o700)
    except Exception:
        pass


def _load_tunnel_state() -> dict[str, Any]:
    _ensure_tunnel_state_dir()
    state = read_json(TUNNEL_STATE_FILE, default={})
    if "client_id" not in state:
        state["client_id"] = ""
    if "current_tunnel" not in state:
        state["current_tunnel"] = None
    if "pending_invoice" not in state:
        state["pending_invoice"] = None
    return state


def _save_tunnel_state(state: dict[str, Any]):
    _ensure_tunnel_state_dir()
    write_secure_json(TUNNEL_STATE_FILE, state, mode=0o600)


def _get_or_create_tunnel_client_id() -> tuple[str, dict[str, Any]]:
    state = _load_tunnel_state()
    client_id = state.get("client_id", "")
    if client_id:
        return client_id, state

    client_id = generate_client_id()
    state["client_id"] = client_id
    _save_tunnel_state(state)
    return client_id, state


def _tunnel_service_status() -> str:
    if DEV_MODE:
        return "inactive"
    try:
        result = subprocess.run(
            ["systemctl", "is-active", f"{TUNNEL_SERVICE_NAME}.service"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _lnpro_request(method: str, endpoint: str, json_body: dict[str, Any] | None = None):
    import requests

    url = f"{TUNNEL_API_BASE_URL}/{endpoint.lstrip('/')}"
    return requests.request(method, url, json=json_body, timeout=20)


def _normalize_tunnel(remote: dict[str, Any]) -> dict[str, Any]:
    return {
        "tunnel_id": remote.get("tunnel_id"),
        "subdomain": remote.get("subdomain"),
        "remote_port": remote.get("remote_port"),
        "ssh_user": remote.get("ssh_user") or TUNNEL_SSH_USER_FALLBACK,
        "ssh_host": remote.get("ssh_host") or TUNNEL_SSH_HOST_FALLBACK,
        "public_url": remote.get("public_url"),
        "expires_at": remote.get("expires_at"),
        "status": remote.get("status", "unknown"),
        "client_note": remote.get("client_note"),
    }


def _sync_tunnel_state_from_remote(state: dict[str, Any], client_id: str) -> dict[str, Any]:
    if DEV_MODE:
        return state
    try:
        resp = _lnpro_request("GET", f"tunnels/client/{client_id}")
        if not resp.ok:
            return state
        payload = resp.json()
        if not isinstance(payload, list):
            return state
        canonical = select_canonical_tunnel(payload)
        if canonical:
            canonical_local = _normalize_tunnel(canonical)
            state["current_tunnel"] = canonical_local
            if is_pending_invoice_paid(state.get("pending_invoice"), canonical_local):
                state["pending_invoice"] = None
            _save_tunnel_state(state)
    except Exception:
        pass
    return state


def _refresh_tunnel_state_from_remote(client_id: str):
    try:
        state = _load_tunnel_state()
        _sync_tunnel_state_from_remote(state, client_id)
    finally:
        with _tunnel_remote_sync_lock:
            _tunnel_remote_sync["in_flight"] = False
            _tunnel_remote_sync["last_finished_at"] = time.monotonic()


def _schedule_tunnel_state_refresh(client_id: str):
    if DEV_MODE:
        return
    now = time.monotonic()
    with _tunnel_remote_sync_lock:
        if _tunnel_remote_sync["in_flight"]:
            return
        last_attempt = max(
            _tunnel_remote_sync["last_started_at"],
            _tunnel_remote_sync["last_finished_at"],
        )
        if last_attempt and (now - last_attempt) < TUNNEL_REMOTE_SYNC_MIN_INTERVAL:
            return
        _tunnel_remote_sync["in_flight"] = True
        _tunnel_remote_sync["last_started_at"] = now
    threading.Thread(
        target=_refresh_tunnel_state_from_remote,
        args=(client_id,),
        daemon=True,
    ).start()


def _build_tunnel_status_payload(client_id: str, state: dict[str, Any]) -> dict[str, Any]:
    current = state.get("current_tunnel")
    return {
        "client_id": client_id,
        "current_tunnel": current,
        "pending_invoice": state.get("pending_invoice"),
        "service_status": _tunnel_service_status(),
        "connect_script": _tunnel_connect_script(current),
        "has_key": TUNNEL_KEY_FILE.exists(),
    }


def _write_key_file(private_key: str):
    _ensure_tunnel_state_dir()
    TUNNEL_KEY_FILE.write_text(private_key, encoding="utf-8")
    os.chmod(TUNNEL_KEY_FILE, 0o600)


def _read_key_file() -> str | None:
    try:
        return TUNNEL_KEY_FILE.read_text(encoding="utf-8")
    except Exception:
        return None


def _read_spark_mnemonic() -> str | None:
    try:
        mnemonic = SPARK_MNEMONIC_FILE.read_text(encoding="utf-8").strip()
        return mnemonic or None
    except Exception:
        return None


def _normalize_mnemonic(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _write_spark_mnemonic(mnemonic: str):
    SPARK_MNEMONIC_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=".mnemonic.",
        dir=str(SPARK_MNEMONIC_FILE.parent),
        text=True,
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(mnemonic + "\n")
        os.chmod(tmp_path, 0o640)
        try:
            spark_gid = grp.getgrnam("spark-sidecar").gr_gid
            os.chown(tmp_path, 0, spark_gid)
        except KeyError:
            pass
        tmp_path.replace(SPARK_MNEMONIC_FILE)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def _runtime_env_content(tunnel: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"REMOTE_PORT={int(tunnel.get('remote_port', 0))}",
            f"SSH_USER={shlex.quote(str(tunnel.get('ssh_user') or TUNNEL_SSH_USER_FALLBACK))}",
            f"SSH_HOST={shlex.quote(str(tunnel.get('ssh_host') or TUNNEL_SSH_HOST_FALLBACK))}",
            f"KEY_FILE={shlex.quote(str(TUNNEL_KEY_FILE))}",
            f"LOCAL_PORT={TUNNEL_LOCAL_PORT}",
            "AUTOSSH_GATETIME=0",
            "AUTOSSH_POLL=30",
            "AUTOSSH_FIRST_POLL=30",
        ]
    ) + "\n"


def _write_runtime_env(tunnel: dict[str, Any]):
    _ensure_tunnel_state_dir()
    TUNNEL_RUNTIME_ENV.write_text(_runtime_env_content(tunnel), encoding="utf-8")
    os.chmod(TUNNEL_RUNTIME_ENV, 0o600)


def _tunnel_connect_script(tunnel: dict[str, Any] | None) -> str | None:
    if not tunnel:
        return None
    private_key = _read_key_file()
    if not private_key:
        return None
    return build_connect_script(private_key, tunnel, local_port=TUNNEL_LOCAL_PORT)


# ── Recovery Helpers ────────────────────────────────────────────────

def _ensure_recovery_state_dir():
    RECOVERY_STATE_DIR.mkdir(parents=True, exist_ok=True)
    RECOVERY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(RECOVERY_STATE_DIR, 0o700)
        os.chmod(RECOVERY_BACKUP_DIR, 0o700)
    except Exception:
        pass


def _recovery_state() -> dict[str, Any]:
    _ensure_recovery_state_dir()
    state = read_json_file(RECOVERY_STATE_FILE, default={})
    state.setdefault("last_backup", None)
    state.setdefault("last_validation", None)
    state.setdefault("last_restore", None)
    return state


def _save_recovery_state(state: dict[str, Any]):
    _ensure_recovery_state_dir()
    write_json_file(RECOVERY_STATE_FILE, state)
    try:
        os.chmod(RECOVERY_STATE_FILE, 0o600)
    except Exception:
        pass


def _default_schedule() -> dict[str, Any]:
    return {
        "enabled": False,
        "interval_hours": 24,
        "backup_type": "full",
        "destination": "local",
        "passphrase": "",
        "last_run_at": None,
        "next_run_at": None,
        "last_result": None,
    }


def _recovery_schedule() -> dict[str, Any]:
    _ensure_recovery_state_dir()
    schedule = read_json_file(RECOVERY_SCHEDULE_FILE, default={})
    result = _default_schedule()
    result.update(schedule)
    return result


def _save_recovery_schedule(schedule: dict[str, Any]):
    _ensure_recovery_state_dir()
    write_json_file(RECOVERY_SCHEDULE_FILE, schedule)
    try:
        os.chmod(RECOVERY_SCHEDULE_FILE, 0o600)
    except Exception:
        pass

def _list_recovery_destinations() -> dict[str, dict[str, Any]]:
    return dict(RECOVERY_DESTINATIONS)


def _resolve_recovery_destination(destination_id: str) -> tuple[str, Path]:
    destinations = _list_recovery_destinations()
    selected = destinations.get(destination_id)
    if not selected:
        raise ValueError("Unknown backup destination.")
    if not selected.get("writable", True):
        raise ValueError(selected.get("reason") or "Selected backup destination is not writable.")
    path = Path(selected["path"])
    path.mkdir(parents=True, exist_ok=True)
    return selected["label"], path


def _archive_entry(archive_path: str, destination_path: Path) -> dict[str, Any] | None:
    try:
        data = destination_path.read_bytes()
    except FileNotFoundError:
        return None
    mode = None
    try:
        mode = oct(destination_path.stat().st_mode & 0o777)
    except Exception:
        pass
    return {
        "archive_path": archive_path,
        "destination_path": str(destination_path),
        "content": data,
        "size": len(data),
        "sha256": file_sha256(data),
        "mode": mode,
    }


def _recovery_component_sources() -> dict[str, list[tuple[str, Path]]]:
    return {
        "database": [
            ("database/database.sqlite3", LNBITS_DB_PATH),
        ],
        "spark": [
            ("spark/mnemonic", SPARK_MNEMONIC_FILE),
            ("spark/api-key.env", Path("/var/lib/spark-sidecar/api-key.env") if not DEV_MODE else Path("/tmp/lnbitspi-test/spark-sidecar/api-key.env")),
        ],
        "config": [
            ("config/lnbits.env", Path("/etc/lnbits/lnbits.env") if not DEV_MODE else Path("/tmp/lnbitspi-test/lnbits-config/lnbits.env")),
            ("config/version.txt", VERSION_FILE),
        ],
        "tunnel": [
            ("tunnel/state.json", TUNNEL_STATE_FILE),
            ("tunnel/reverse-proxy-key", TUNNEL_KEY_FILE),
            ("tunnel/runtime.env", TUNNEL_RUNTIME_ENV),
        ],
        "wifi": [
            ("wifi/wpa_supplicant.conf", WPA_SUPPLICANT_CONF),
        ],
        "tor": [
            ("tor/hostname", TOR_HOSTNAME_FILE),
        ],
        "update": [
            ("update/status", UPDATE_STATE_DIR / "status"),
            ("update/target-version", UPDATE_STATE_DIR / "target-version"),
        ],
    }


def _allowed_recovery_paths() -> dict[str, tuple[str, Path]]:
    allowed = {}
    for component, sources in _recovery_component_sources().items():
        for archive_path, destination_path in sources:
            allowed[archive_path] = (component, destination_path)
    return allowed


def _backup_component_payloads(backup_type: str) -> dict[str, list[dict[str, Any]]]:
    component_sources = _recovery_component_sources()
    included = {"database", "spark", "config", "tunnel"}
    if backup_type == "full":
        included.update({"wifi", "tor", "update"})
    payloads: dict[str, list[dict[str, Any]]] = {}
    for component, sources in component_sources.items():
        if component not in included:
            continue
        entries = []
        for archive_path, destination_path in sources:
            entry = _archive_entry(archive_path, destination_path)
            if entry:
                entries.append(entry)
        if entries:
            payloads[component] = entries
    return payloads


def _recovery_manifest(backup_type: str, encrypted: bool, payloads: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return build_backup_manifest(
        backup_type=backup_type,
        current_version=get_current_version(),
        encrypted=encrypted,
        components=payloads,
        spark_seed_present=bool(_read_spark_mnemonic()),
        tunnel_configured=bool((_load_tunnel_state().get("current_tunnel") or {}).get("tunnel_id")),
        created_by="manual",
    )


def _create_recovery_backup_bytes(backup_type: str, passphrase: str | None = None, *, created_by: str = "manual") -> tuple[bytes, dict[str, Any]]:
    services = _services_for_restore(list({"database", "spark", "tunnel"} if backup_type == "full" else {"database"}))
    try:
        _stop_services(services)
        payloads = _backup_component_payloads(backup_type)
        manifest = _recovery_manifest(backup_type, bool(passphrase), payloads)
        manifest["created_by"] = created_by
        plain_backup = package_plain_backup(manifest, payloads)
        if passphrase:
            container = package_encrypted_backup(manifest, plain_backup, passphrase)
        else:
            container = plain_backup
        return container, manifest
    finally:
        _start_services(services)


def _backup_filename(manifest: dict[str, Any]) -> str:
    ts = manifest["created_at"].replace(":", "").replace("-", "").replace("+00:00", "Z")
    return f"lnbitsbox-recovery-{manifest['backup_type']}-{ts}.zip"


def _record_backup_success(*, manifest: dict[str, Any], storage: str, file_path: str | None, validated: bool):
    state = _recovery_state()
    state["last_backup"] = {
        "created_at": manifest["created_at"],
        "type": manifest["backup_type"],
        "encrypted": manifest["encrypted"],
        "components": manifest["components"],
        "storage": storage,
        "file_path": file_path,
        "validated": validated,
        "version": manifest["lnbitsbox_version"],
    }
    state["last_validation"] = {
        "checked_at": utc_now_iso(),
        "status": "ok" if validated else "unknown",
        "message": "Backup archive passed integrity checks." if validated else "Backup archive created.",
    }
    _save_recovery_state(state)


def _write_recovery_destination_file(destination_id: str, content: bytes, manifest: dict[str, Any]) -> dict[str, Any]:
    label, destination = _resolve_recovery_destination(destination_id)
    file_name = _backup_filename(manifest)
    target = destination / file_name
    target.write_bytes(content)
    try:
        os.chmod(target, 0o600)
    except Exception:
        pass
    _record_backup_success(
        manifest=manifest,
        storage=label,
        file_path=str(target),
        validated=True,
    )
    return {
        "destination": label,
        "path": str(target),
        "filename": file_name,
    }


def _read_local_backup(local_backup: str) -> tuple[str, bytes]:
    requested = Path(local_backup).name
    target = RECOVERY_BACKUP_DIR / requested
    if not target.exists() or not target.is_file():
        raise ValueError("Selected local backup was not found.")
    return requested, target.read_bytes()


def _load_recovery_backup(passphrase: str | None = None):
    local_backup = (request.form.get("local_backup") or "").strip()
    if local_backup:
        filename, archive_bytes = _read_local_backup(local_backup)
    else:
        if "file" not in request.files:
            raise ValueError("Choose a saved backup on this box or upload a backup file.")
        upload = request.files["file"]
        if not upload.filename:
            raise ValueError("No backup file selected.")
        filename = upload.filename
        archive_bytes = upload.read()
        if not archive_bytes:
            raise ValueError("Uploaded backup is empty.")
    manifest, inner_zip = load_backup_container(archive_bytes, passphrase=passphrase)
    issues = validate_manifest_files(manifest, inner_zip)
    compatibility = compatibility_report(get_current_version(), manifest.get("lnbitsbox_version", ""))
    return filename, archive_bytes, manifest, inner_zip, issues, compatibility


def _write_restored_file(destination_path: Path, payload: bytes, mode_value: str | None = None):
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(destination_path.parent))
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
    tmp_path = Path(tmp_name)
    try:
        if mode_value:
            os.chmod(tmp_path, int(mode_value, 8))
        elif destination_path.exists():
            os.chmod(tmp_path, stat.S_IMODE(destination_path.stat().st_mode))
        tmp_path.replace(destination_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def _services_for_restore(components: list[str]) -> list[str]:
    services = set()
    if any(component in components for component in ("database", "config")):
        services.add("lnbits.service")
    if "spark" in components:
        services.add("spark-sidecar.service")
    if "tunnel" in components:
        services.add(f"{TUNNEL_SERVICE_NAME}.service")
    return sorted(services)


def _stop_services(service_names: list[str]):
    if DEV_MODE:
        return
    for service in service_names:
        subprocess.run(["systemctl", "stop", service], capture_output=True, timeout=30, check=False)


def _start_services(service_names: list[str]):
    if DEV_MODE:
        return
    for service in service_names:
        subprocess.run(["systemctl", "start", service], capture_output=True, timeout=30, check=False)


def _restore_component_files(inner_zip: zipfile.ZipFile, manifest: dict[str, Any], selected_components: list[str]) -> dict[str, Any]:
    restored_files = []
    allowed_paths = _allowed_recovery_paths()
    for file_info in manifest.get("files", []):
        component = file_info.get("component")
        if component not in selected_components:
            continue
        archive_path = file_info.get("archive_path")
        allowed = allowed_paths.get(archive_path)
        if not allowed:
            raise ValueError(f"Archive contains unsupported restore path: {archive_path}")
        allowed_component, destination_path = allowed
        if allowed_component != component:
            raise ValueError(f"Archive component mismatch for {archive_path}")
        payload = inner_zip.read(archive_path)
        _write_restored_file(destination_path, payload, file_info.get("mode"))
        restored_files.append({
            "component": component,
            "path": str(destination_path),
        })
        try:
            if destination_path == LNBITS_DB_PATH:
                shutil.chown(destination_path, user="lnbits", group="lnbits")
            elif destination_path in (SPARK_MNEMONIC_FILE, Path("/var/lib/spark-sidecar/api-key.env"), Path("/tmp/lnbitspi-test/spark-sidecar/api-key.env")):
                shutil.chown(destination_path, user="root", group="spark-sidecar")
            elif destination_path in (TUNNEL_STATE_FILE, TUNNEL_KEY_FILE, TUNNEL_RUNTIME_ENV):
                shutil.chown(destination_path, user="root", group="root")
        except Exception:
            pass
    return {"restored_files": restored_files}


def _post_restore_report(selected_components: list[str], manifest: dict[str, Any]) -> dict[str, Any]:
    checks = []
    for component in selected_components:
        checks.append({
            "component": component,
            "label": RECOVERY_COMPONENT_LABELS.get(component, component),
            "ok": component != "database" or LNBITS_DB_PATH.exists(),
        })
    compatibility = compatibility_report(get_current_version(), manifest.get("lnbitsbox_version", ""))
    return {
        "checked_at": utc_now_iso(),
        "checks": checks,
        "compatibility": compatibility,
        "services": {
            "lnbits": get_service_status("lnbits"),
            "spark-sidecar": get_service_status("spark-sidecar"),
            TUNNEL_SERVICE_NAME: _tunnel_service_status(),
        },
    }


def _recovery_status_payload() -> dict[str, Any]:
    state = _recovery_state()
    destinations = _list_recovery_destinations()
    schedule = _recovery_schedule()
    schedule["passphrase"] = "configured" if schedule.get("passphrase") else ""
    return {
        "spark_seed_present": bool(_read_spark_mnemonic()),
        "tunnel_ready": TUNNEL_KEY_FILE.exists(),
        "last_backup": state.get("last_backup"),
        "last_validation": state.get("last_validation"),
        "last_restore": state.get("last_restore"),
        "schedule": schedule,
        "destinations": [
            {
                "id": key,
                "label": value["label"],
                "path": str(value["path"]),
                "writable": value.get("writable", True),
                "reason": value.get("reason", ""),
                "detail": value.get("detail", f"Saved to {value['path']}"),
            }
            for key, value in destinations.items()
        ],
        "recommended_actions": [
            "Create an encrypted full backup before updating or replacing the SD card.",
            "Keep the Spark seed phrase stored separately from device backups.",
            "Restore only the components you intend to replace on this box.",
        ],
        "saved_backups": _recovery_backup_files(),
    }


def _manifest_path_issues(manifest: dict[str, Any]) -> list[str]:
    allowed_paths = _allowed_recovery_paths()
    issues = []
    for file_info in manifest.get("files", []):
        archive_path = file_info.get("archive_path")
        component = file_info.get("component")
        allowed = allowed_paths.get(archive_path)
        if not allowed:
            issues.append(f"Unsupported archive path: {archive_path}")
            continue
        allowed_component, allowed_destination = allowed
        if component != allowed_component:
            issues.append(f"Component mismatch for {archive_path}")
        if file_info.get("destination_path") != str(allowed_destination):
            issues.append(f"Destination mismatch for {archive_path}")
    return issues


def _recovery_backup_files() -> list[dict[str, Any]]:
    _ensure_recovery_state_dir()
    backups = []
    for path in sorted(RECOVERY_BACKUP_DIR.glob("lnbitsbox-recovery-*.zip"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            stat_result = path.stat()
        except FileNotFoundError:
            continue
        backups.append({
            "filename": path.name,
            "path": str(path),
            "size": stat_result.st_size,
            "modified_at": datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
        })
    return backups


def _local_backup_manifest(path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            return json.loads(archive.read("manifest.json"))
    except Exception:
        return None


def _prune_scheduled_backups():
    now = datetime.now().astimezone()
    checkpoints = [
        ("daily", now.timestamp() - 86400),
        ("weekly", now.timestamp() - (7 * 86400)),
        ("monthly", now.timestamp() - (30 * 86400)),
    ]
    keep: set[Path] = set()
    candidates: list[tuple[Path, float]] = []

    for path in RECOVERY_BACKUP_DIR.glob("lnbitsbox-recovery-*.zip"):
        manifest = _local_backup_manifest(path)
        if not manifest or manifest.get("created_by") != "scheduled":
            continue
        created_at = parse_iso_datetime(manifest.get("created_at"))
        if created_at is None:
            continue
        candidates.append((path, created_at.timestamp()))

    if not candidates:
        return

    candidates.sort(key=lambda item: item[1], reverse=True)
    keep.add(candidates[0][0])

    for _, threshold in checkpoints:
        eligible = [item for item in candidates if item[1] <= threshold]
        if eligible:
            keep.add(max(eligible, key=lambda item: item[1])[0])

    for path, _ in candidates:
        if path in keep:
            continue
        try:
            path.unlink()
        except OSError:
            pass


def _scheduled_backup_worker():
    while True:
        try:
            schedule = _recovery_schedule()
            if schedule.get("enabled"):
                interval_hours = max(1, int(schedule.get("interval_hours") or 24))
                now = time.time()
                next_run_at = schedule.get("next_run_at")
                if not next_run_at or now >= float(next_run_at):
                    passphrase = schedule.get("passphrase", "")
                    if not passphrase:
                        raise ValueError("Scheduled backup passphrase is missing.")
                    content, manifest = _create_recovery_backup_bytes(
                        schedule.get("backup_type", "full"),
                        passphrase=passphrase,
                        created_by="scheduled",
                    )
                    backup_result = _write_recovery_destination_file(
                        schedule.get("destination", "local"),
                        content,
                        manifest,
                    )
                    _prune_scheduled_backups()
                    schedule["last_run_at"] = now
                    schedule["next_run_at"] = now + (interval_hours * 3600)
                    schedule["last_result"] = {
                        "status": "ok",
                        "message": f"Last scheduled backup saved to {backup_result['path']}",
                        "created_at": manifest["created_at"],
                    }
                    _save_recovery_schedule(schedule)
        except Exception as exc:
            schedule = _recovery_schedule()
            schedule["last_result"] = {
                "status": "error",
                "message": str(exc),
                "created_at": utc_now_iso(),
            }
            _save_recovery_schedule(schedule)
        time.sleep(60)


# ── Network Helpers ─────────────────────────────────────────────────

def get_wifi_interface():
    """Detect wireless interface name by checking /sys/class/net/*/wireless"""
    try:
        for iface in Path("/sys/class/net").iterdir():
            if (iface / "wireless").exists():
                return iface.name
    except Exception:
        pass
    return None


def wpa_cli(iface, *args, timeout=5, check=False):
    """Run wpa_cli via control socket (not D-Bus) with stdin closed"""
    return subprocess.run(
        ["wpa_cli", "-p", "/run/wpa_supplicant", "-i", iface, *args],
        capture_output=True, text=True, timeout=timeout,
        stdin=subprocess.DEVNULL, check=check,
    )


def get_network_info():
    """Return network connectivity info: internet, wifi, ethernet"""
    if DEV_MODE:
        return {
            "internet": True,
            "wifi": {"ssid": "HomeNetwork", "ip": "192.168.1.100", "interface": "wlan0"},
            "ethernet": {"interface": "eth0", "ip": "192.168.1.50"},
        }
    info = {"internet": False, "wifi": None, "ethernet": None}

    # Internet check — ping 1.1.1.1
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "1.1.1.1"],
            capture_output=True, timeout=5,
        )
        info["internet"] = result.returncode == 0
    except Exception:
        pass

    # WiFi — via wpa_cli status
    wifi_iface = get_wifi_interface()
    if wifi_iface:
        try:
            result = wpa_cli(wifi_iface, "status")
            if result.returncode == 0:
                wpa = {}
                for line in result.stdout.strip().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        wpa[k] = v
                if wpa.get("wpa_state") == "COMPLETED":
                    info["wifi"] = {
                        "ssid": wpa.get("ssid", ""),
                        "ip": wpa.get("ip_address", ""),
                        "interface": wifi_iface,
                    }
        except Exception:
            pass

    # Ethernet — via ip -j addr show
    try:
        result = subprocess.run(
            ["ip", "-j", "addr", "show"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            ifaces = json.loads(result.stdout)
            for iface in ifaces:
                name = iface.get("ifname", "")
                if not (name.startswith("eth") or name.startswith("en")):
                    continue
                for addr_info in iface.get("addr_info", []):
                    if addr_info.get("family") == "inet":
                        info["ethernet"] = {
                            "interface": name,
                            "ip": addr_info.get("local", ""),
                        }
                        break
                if info["ethernet"]:
                    break
    except Exception:
        pass

    return info


# ── Authentication ──────────────────────────────────────────────────

def authenticate(username, password):
    """Verify password against /etc/shadow (requires root)"""
    if DEV_MODE:
        return True
    if crypt is None:
        return False
    try:
        with open("/etc/shadow") as f:
            for line in f:
                fields = line.strip().split(":")
                if fields[0] == username and len(fields) > 1 and fields[1]:
                    return crypt.crypt(password, fields[1]) == fields[1]
    except Exception:
        pass
    return False


# ── Login Rate Limiting ─────────────────────────────────────────────
# Exponential backoff: after 5 failures, lock out for 30s, doubling each time

LOGIN_MAX_ATTEMPTS = 5
LOGIN_BASE_LOCKOUT = 30  # seconds
_login_attempts = {}  # ip -> {"failures": int, "locked_until": float}
_login_attempts_lock = threading.Lock()


def _check_rate_limit(ip):
    """Return seconds remaining if locked out, else 0."""
    with _login_attempts_lock:
        entry = _login_attempts.get(ip)
        if not entry:
            return 0
        if entry["failures"] < LOGIN_MAX_ATTEMPTS:
            return 0
        remaining = entry["locked_until"] - time.monotonic()
        return max(0, remaining)


def _record_failure(ip):
    with _login_attempts_lock:
        entry = _login_attempts.setdefault(ip, {"failures": 0, "locked_until": 0})
        entry["failures"] += 1
        if entry["failures"] >= LOGIN_MAX_ATTEMPTS:
            # Exponential backoff: 30s, 60s, 120s, ...
            exponent = entry["failures"] - LOGIN_MAX_ATTEMPTS
            lockout = LOGIN_BASE_LOCKOUT * (2 ** min(exponent, 8))
            entry["locked_until"] = time.monotonic() + lockout


def _clear_failures(ip):
    with _login_attempts_lock:
        _login_attempts.pop(ip, None)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if DEV_MODE or session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for("login"))
    return decorated


# ── Stats Collection ────────────────────────────────────────────────

def get_cpu_temp():
    try:
        temp = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return round(int(temp) / 1000, 1)
    except Exception:
        return None


def get_uptime():
    try:
        secs = float(Path("/proc/uptime").read_text().split()[0])
        days = int(secs // 86400)
        hours = int((secs % 86400) // 3600)
        minutes = int((secs % 3600) // 60)
        return {"seconds": secs, "formatted": f"{days}d {hours}h {minutes}m"}
    except Exception:
        return {"seconds": 0, "formatted": "unknown"}


def get_service_status(service):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", f"{service}.service"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def get_spark_balance():
    """Query Spark sidecar for wallet balance"""
    try:
        import requests
        headers = {"X-API-KEY": SPARK_SIDECAR_API_KEY}
        resp = requests.post(f"{SPARK_URL}/v1/balance", headers=headers, timeout=5)
        if resp.ok:
            data = resp.json()
            balance_msat = data.get("balance_msat")
            if balance_msat is not None:
                return {"balance": int(balance_msat) // 1000}
            balance_sats = data.get("balance_sats")
            if balance_sats is not None:
                return {"balance": int(balance_sats)}
    except Exception:
        pass
    return None


def get_cpu_percent():
    try:
        import psutil
        return psutil.cpu_percent(interval=0)
    except Exception:
        return 0


def get_memory_info():
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "used": mem.used,
            "total": mem.total,
            "percent": mem.percent,
        }
    except Exception:
        return {"used": 0, "total": 0, "percent": 0}


def get_lnbits_http_status():
    """Check LNbits by making an HTTP request to /"""
    try:
        import requests
        resp = requests.get(f"{LNBITS_URL}/", timeout=3, allow_redirects=True)
        return resp.status_code
    except Exception:
        return None


def get_onion_address():
    """Read the Tor hidden service .onion address"""
    try:
        return Path("/var/lib/tor/onion/lnbits/hostname").read_text().strip()
    except Exception:
        return None


def collect_stats():
    """Collect all system stats"""
    disk = shutil.disk_usage("/")
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": get_cpu_percent(),
        "ram": get_memory_info(),
        "cpu_temp": get_cpu_temp(),
        "disk": {
            "used": disk.used,
            "total": disk.total,
            "percent": round(disk.used / disk.total * 100, 1) if disk.total else 0,
        },
        "uptime": get_uptime(),
        "services": {
            svc: get_service_status(svc) for svc in ALLOWED_SERVICES
        },
        "spark_balance": get_spark_balance(),
        "tor_onion": get_onion_address(),
        "network": get_network_info(),
    }


def stats_collector():
    """Background thread collecting stats periodically"""
    # Initial collection with small delay for psutil baseline
    try:
        import psutil
        psutil.cpu_percent()
    except Exception:
        pass
    time.sleep(1)

    while True:
        try:
            stats = collect_stats()
            with stats_lock:
                stats_history.append(stats)
        except Exception:
            pass
        time.sleep(STATS_INTERVAL)


# Start background collector
threading.Thread(target=stats_collector, daemon=True).start()
threading.Thread(target=_scheduled_backup_worker, daemon=True).start()


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/box/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))

    ip = request.remote_addr or "unknown"

    if request.method == "POST":
        lockout = _check_rate_limit(ip)
        if lockout > 0:
            flash(f"Too many attempts. Try again in {int(lockout)}s.", "error")
            return render_template("login.html"), 429

        password = request.form.get("password", "")

        if authenticate(SSH_USER, password):
            _clear_failures(ip)
            session["authenticated"] = True
            return redirect(url_for("dashboard"))

        _record_failure(ip)
        flash("Invalid password", "error")

    return render_template("login.html")


@app.route("/box/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/box/")
@login_required
def dashboard():
    return _render_admin_page(
        "overview.html",
        page_key="overview",
        page_title="Overview",
        include_tunnel_status=True,
    )


@app.route("/box/remote-access")
@login_required
def remote_access():
    return _render_admin_page(
        "remote_access.html",
        page_key="remote_access",
        page_title="Remote Access",
        include_tunnel_status=True,
    )


@app.route("/box/system")
@login_required
def system_page():
    return _render_admin_page(
        "system.html",
        page_key="system",
        page_title="System",
    )


@app.route("/box/maintenance")
@login_required
def maintenance_page():
    return _render_admin_page(
        "maintenance.html",
        page_key="maintenance",
        page_title="Maintenance",
        page_intro="Create encrypted recovery archives, validate restores before applying them, and schedule protected backups to local or attached storage.",
    )


@app.route("/box/advanced")
@login_required
def advanced_page():
    return _render_admin_page(
        "advanced.html",
        page_key="advanced",
        page_title="Advanced",
        include_tunnel_status=True,
        spark_mnemonic=_read_spark_mnemonic(),
    )


def _render_admin_page(
    template_name: str,
    *,
    page_key: str,
    page_title: str,
    page_intro: str = "",
    include_tunnel_status: bool = False,
    **context,
):
    initial_tunnel_status = None
    if include_tunnel_status:
        client_id, state = _get_or_create_tunnel_client_id()
        initial_tunnel_status = _build_tunnel_status_payload(client_id, state)
        initial_tunnel_status["service_status"] = "unknown"
    return render_template(
        template_name,
        dev_mode=DEV_MODE,
        active_page=page_key,
        page_title=page_title,
        page_intro=page_intro,
        version=get_current_version(),
        initial_tunnel_status=initial_tunnel_status,
        **context,
    )


@app.route("/box/api/stats")
@login_required
def api_stats():
    current = collect_stats()
    with stats_lock:
        history = list(stats_history)
    payload = {
        "current": current,
        "history": {
            "timestamps": [s["timestamp"] for s in history],
            "cpu": [s["cpu_percent"] for s in history],
            "ram": [s["ram"]["percent"] for s in history],
            "temp": [s["cpu_temp"] for s in history],
        }
    }
    return _json_response(data=payload, **payload)


@app.route("/box/api/lnbits-status")
@login_required
def api_lnbits_status():
    code = get_lnbits_http_status()
    if code == 200:
        return _json_response(data={"status": "running"}, status="running")
    elif code == 502:
        return _json_response(data={"status": "starting"}, status="starting")
    elif code is not None:
        return _json_response(data={"status": "error", "code": code}, status="error", code=code)
    else:
        return _json_response(data={"status": "stopped"}, status="stopped")


@app.route("/box/api/shutdown", methods=["POST"])
@login_required
def api_shutdown():
    if DEV_MODE:
        return jsonify({"status": "ok", "message": "DEV MODE: would shutdown"})
    subprocess.Popen(["systemd-run", "--no-block", "systemctl", "poweroff"])
    return jsonify({"status": "ok", "message": "Shutting down..."})


@app.route("/box/api/reboot", methods=["POST"])
@login_required
def api_reboot():
    if DEV_MODE:
        return jsonify({"status": "ok", "message": "DEV MODE: would reboot"})
    subprocess.Popen(["systemd-run", "--no-block", "systemctl", "reboot"])
    return jsonify({"status": "ok", "message": "Rebooting..."})


@app.route("/box/api/restart/<service>", methods=["POST"])
@login_required
def api_restart_service(service):
    return _service_action(service, "restart", "restarting")


@app.route("/box/api/start/<service>", methods=["POST"])
@login_required
def api_start_service(service):
    return _service_action(service, "start", "starting")


@app.route("/box/api/stop/<service>", methods=["POST"])
@login_required
def api_stop_service(service):
    return _service_action(service, "stop", "stopping")


@app.route("/box/api/spark/seed", methods=["POST"])
@login_required
def api_update_spark_seed():
    payload = request.get_json(silent=True) or {}
    new_mnemonic = _normalize_mnemonic(str(payload.get("mnemonic", "")))

    if not new_mnemonic:
        return _json_error("Enter a seed phrase.", 400)

    words = new_mnemonic.split()
    if len(words) != 12:
        return _json_error("Enter exactly 12 words.", 400)

    if not Mnemonic("english").check(new_mnemonic):
        return _json_error("Enter a valid 12-word BIP39 seed phrase.", 400)

    current_mnemonic = _normalize_mnemonic(_read_spark_mnemonic() or "")
    if current_mnemonic and new_mnemonic == current_mnemonic:
        return _json_error("That seed phrase is already in use.", 400)

    if DEV_MODE:
        _write_spark_mnemonic(new_mnemonic)
        return _json_response(
            status="ok",
            message="Spark seed phrase updated successfully. Spark is restarting now.",
            data={"service": "spark-sidecar", "action": "restart"},
        )

    try:
        _write_spark_mnemonic(new_mnemonic)
        subprocess.run(
            ["systemctl", "restart", "spark-sidecar.service"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return _json_response(
            status="ok",
            message="Spark seed phrase updated successfully. Spark is restarting now.",
            data={"service": "spark-sidecar", "action": "restart"},
        )
    except subprocess.CalledProcessError as e:
        return _json_error(e.stderr.decode() or "Failed to restart Spark.", 500)
    except Exception as e:
        return _json_error(str(e), 500)


def _service_action(service, action, verb):
    if service not in ALLOWED_SERVICES:
        return _json_error("Invalid service", 400)

    if DEV_MODE:
        return _json_response(status="ok", message=f"DEV MODE: would {action} {service}", data={"service": service, "action": action})

    try:
        subprocess.run(
            ["systemctl", action, f"{service}.service"],
            check=True, capture_output=True, timeout=30
        )
        return _json_response(status="ok", message=f"{service} is {verb}", data={"service": service, "action": action})
    except subprocess.CalledProcessError as e:
        return _json_error(e.stderr.decode(), 500)


# ── Recovery Center ──────────────────────────────────────────

@app.route("/box/api/recovery/status")
@login_required
def api_recovery_status():
    payload = _recovery_status_payload()
    return _json_response(status="ok", data=payload, **payload)


@app.route("/box/api/recovery/backups")
@login_required
def api_recovery_backups():
    payload = {"backups": _recovery_backup_files()}
    return _json_response(status="ok", data=payload, **payload)


@app.route("/box/api/recovery/backups/<path:filename>")
@login_required
def api_recovery_backup_file_download(filename: str):
    safe_name = Path(filename).name
    target = RECOVERY_BACKUP_DIR / safe_name
    if not target.exists() or not target.is_file():
        return _json_error("Backup file not found.", 404)
    return send_file(
        target,
        mimetype="application/zip",
        as_attachment=True,
        download_name=safe_name,
    )


@app.route("/box/api/recovery/backup/download", methods=["POST"])
@login_required
def api_recovery_backup_download():
    backup_type = (request.form.get("backup_type") or "full").strip().lower()
    passphrase = request.form.get("passphrase", "")
    if backup_type not in ("quick", "full"):
        return _json_error("Invalid backup type", 400)
    if not passphrase:
        return _json_error("Backup password is required.", 400)

    content, manifest = _create_recovery_backup_bytes(backup_type, passphrase=passphrase)
    _record_backup_success(
        manifest=manifest,
        storage="Downloaded from browser",
        file_path=None,
        validated=True,
    )
    response = send_file(
        io.BytesIO(content),
        mimetype="application/zip",
        as_attachment=True,
        download_name=_backup_filename(manifest),
    )
    return response


@app.route("/box/api/recovery/backup/save", methods=["POST"])
@login_required
def api_recovery_backup_save():
    payload = request.get_json(silent=True) or {}
    backup_type = str(payload.get("backup_type") or "full").strip().lower()
    passphrase = str(payload.get("passphrase") or "")
    if backup_type not in ("quick", "full"):
        return _json_error("Invalid backup type", 400)
    if not passphrase:
        return _json_error("Backup password is required.", 400)

    content, manifest = _create_recovery_backup_bytes(backup_type, passphrase=passphrase)
    result = _write_recovery_destination_file("local", content, manifest)
    return _json_response(
        status="ok",
        message=f"Encrypted backup saved on this box at {result['path']}",
        data=result,
        **result,
    )


@app.route("/box/api/recovery/restore/validate", methods=["POST"])
@login_required
def api_recovery_restore_validate():
    passphrase = request.form.get("passphrase", "")
    try:
        filename, _, manifest, inner_zip, issues, compatibility = _load_recovery_backup(passphrase=passphrase)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except Exception as exc:
        return _json_error(str(exc), 500)

    issues.extend(_manifest_path_issues(manifest))
    components = available_restore_components(manifest)
    payload = {
        "filename": filename,
        "manifest": manifest,
        "components": components,
        "issues": issues,
        "compatibility": compatibility,
    }
    state = _recovery_state()
    state["last_validation"] = {
        "checked_at": utc_now_iso(),
        "status": "ok" if not issues else "error",
        "message": "Backup validation completed successfully." if not issues else "; ".join(issues),
    }
    _save_recovery_state(state)
    return _json_response(status="ok" if not issues else "error", data=payload, **payload)


@app.route("/box/api/recovery/restore", methods=["POST"])
@login_required
def api_recovery_restore():
    passphrase = request.form.get("passphrase", "")
    selected_components = request.form.getlist("components")
    try:
        filename, _, manifest, inner_zip, issues, compatibility = _load_recovery_backup(passphrase=passphrase)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except Exception as exc:
        return _json_error(str(exc), 500)

    issues.extend(_manifest_path_issues(manifest))
    if issues:
        return _json_error("Backup validation failed: " + "; ".join(issues), 400)

    if compatibility.get("level") == "error":
        return _json_error(compatibility["message"], 400)

    available_components = set(available_restore_components(manifest))
    if not selected_components:
        selected_components = list(available_components)
    invalid_components = [component for component in selected_components if component not in available_components]
    if invalid_components:
        return _json_error("Invalid restore components: " + ", ".join(invalid_components), 400)

    services = _services_for_restore(selected_components)
    try:
        _stop_services(services)
        restore_result = _restore_component_files(inner_zip, manifest, selected_components)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    finally:
        _start_services(services)

    report = _post_restore_report(selected_components, manifest)
    state = _recovery_state()
    state["last_restore"] = {
        "restored_at": utc_now_iso(),
        "filename": filename,
        "components": selected_components,
        "report": report,
    }
    _save_recovery_state(state)
    payload = {
        "filename": filename,
        "restored_components": selected_components,
        "restore_result": restore_result,
        "report": report,
    }
    return _json_response(
        status="ok",
        message="Encrypted backup restored successfully.",
        data=payload,
        **payload,
    )


@app.route("/box/api/recovery/schedule", methods=["GET"])
@login_required
def api_recovery_schedule_get():
    payload = _recovery_schedule()
    payload["passphrase"] = "configured" if payload.get("passphrase") else ""
    return _json_response(status="ok", data=payload, **payload)


@app.route("/box/api/recovery/schedule", methods=["POST"])
@login_required
def api_recovery_schedule_set():
    payload = request.get_json(silent=True) or {}
    enabled = bool(payload.get("enabled"))
    interval_hours = max(1, min(168, int(payload.get("interval_hours") or 24)))
    backup_type = str(payload.get("backup_type") or "full").strip().lower()
    destination = "local"
    passphrase = str(payload.get("passphrase") or "")
    existing = _recovery_schedule()

    if backup_type not in ("quick", "full"):
        return _json_error("Invalid backup type", 400)
    if enabled and not passphrase and not existing.get("passphrase"):
        return _json_error("A backup password is required for scheduled backups.", 400)

    if enabled:
        _resolve_recovery_destination(destination)

    next_run_at = time.time() + (interval_hours * 3600) if enabled else None
    schedule = {
        "enabled": enabled,
        "interval_hours": interval_hours,
        "backup_type": backup_type,
        "destination": destination,
        "passphrase": passphrase or existing.get("passphrase", ""),
        "last_run_at": existing.get("last_run_at"),
        "next_run_at": next_run_at,
        "last_result": existing.get("last_result"),
    }
    _save_recovery_schedule(schedule)
    response_payload = dict(schedule)
    response_payload["passphrase"] = "configured" if schedule.get("passphrase") else ""
    return _json_response(
        status="ok",
        message="Scheduled encrypted backups updated.",
        data=response_payload,
        **response_payload,
    )


# ── Legacy Database Endpoints ─────────────────────────────────

@app.route("/box/api/db/info")
@login_required
def api_db_info():
    if DEV_MODE:
        return _json_response(size=4_520_000, data={"size": 4_520_000})
    try:
        size = LNBITS_DB_PATH.stat().st_size
        return _json_response(size=size, data={"size": size})
    except FileNotFoundError:
        return _json_response(size=0, error="Database file not found", data={"size": 0})
    except Exception as e:
        return _json_error(str(e), 500)


@app.route("/box/api/db/backup", methods=["POST"])
@login_required
def api_db_backup():
    return _json_error(
        "Database-only backups were replaced by encrypted Recovery Center backups. Use /box/maintenance.",
        410,
    )


@app.route("/box/api/db/restore", methods=["POST"])
@login_required
def api_db_restore():
    return _json_error(
        "Database-only restore was replaced by encrypted Recovery Center restore. Use /box/maintenance.",
        410,
    )


# ── WiFi Endpoints ──────────────────────────────────────────────

@app.route("/box/api/wifi/scan", methods=["POST"])
@login_required
def api_wifi_scan():
    if DEV_MODE:
        networks = [
            {"ssid": "HomeNetwork", "signal": -45, "flags": "[WPA2-PSK-CCMP][ESS]"},
            {"ssid": "CoffeeShop_Free", "signal": -62, "flags": "[ESS]"},
            {"ssid": "Neighbor5G", "signal": -70, "flags": "[WPA2-PSK-CCMP][WPS][ESS]"},
            {"ssid": "OfficeWiFi", "signal": -78, "flags": "[WPA2-EAP-CCMP][ESS]"},
        ]
        return _json_response(networks=networks, data={"networks": networks})

    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return _json_error("No wireless interface found", 404)

    try:
        wpa_cli(wifi_iface, "scan")
        time.sleep(3)
        result = wpa_cli(wifi_iface, "scan_results")
        if result.returncode != 0:
            return _json_error("Scan failed", 500)

        # Parse scan results: bssid / frequency / signal / flags / ssid
        networks = {}
        for line in result.stdout.strip().splitlines()[1:]:  # skip header
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            ssid = parts[4].strip()
            if not ssid:
                continue
            signal = int(parts[2])
            flags = parts[3]
            # Deduplicate by SSID, keeping strongest signal
            if ssid not in networks or signal > networks[ssid]["signal"]:
                networks[ssid] = {"ssid": ssid, "signal": signal, "flags": flags}

        sorted_networks = sorted(networks.values(), key=lambda n: n["signal"], reverse=True)
        return _json_response(networks=sorted_networks, data={"networks": sorted_networks})
    except Exception as e:
        return _json_error(str(e), 500)


@app.route("/box/api/wifi/connect", methods=["POST"])
@login_required
def api_wifi_connect():
    data = request.get_json(silent=True) or {}
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "")

    if not ssid:
        return _json_error("SSID is required", 400)

    if DEV_MODE:
        with wifi_connect_lock:
            wifi_connect_status.update({"status": "connecting", "message": f"Connecting to {ssid}...", "ip": ""})

        def mock_connect():
            time.sleep(4)
            with wifi_connect_lock:
                wifi_connect_status.update({"status": "success", "message": f"Connected to {ssid}", "ip": "192.168.1.42"})
        threading.Thread(target=mock_connect, daemon=True).start()
        return _json_response(status="connecting", data={"status": "connecting"})

    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return _json_error("No wireless interface found", 404)

    with wifi_connect_lock:
        if wifi_connect_status["status"] == "connecting":
            return _json_error("Connection attempt already in progress", 409)
        wifi_connect_status.update({"status": "connecting", "message": f"Connecting to {ssid}...", "ip": ""})

    def do_connect():
        global wifi_connect_status
        try:
            # Read backup of current config
            backup_conf = None
            conf_path = "/etc/wpa_supplicant.conf"
            try:
                backup_conf = Path(conf_path).read_text()
            except Exception:
                pass

            # Add network
            result = wpa_cli(wifi_iface, "add_network")
            net_id = result.stdout.strip()

            # Set SSID
            wpa_cli(wifi_iface, "set_network", net_id, "ssid", f'"{ssid}"', check=True)

            # Set password or open network
            if password:
                wpa_cli(wifi_iface, "set_network", net_id, "psk", f'"{password}"', check=True)
            else:
                wpa_cli(wifi_iface, "set_network", net_id, "key_mgmt", "NONE", check=True)

            # Select network (connects to new, disables others)
            wpa_cli(wifi_iface, "select_network", net_id, check=True)

            # Poll for connection
            connected = False
            new_ip = ""
            for _ in range(8):  # 8 * 2s = 16s max
                time.sleep(2)
                result = wpa_cli(wifi_iface, "status")
                wpa = {}
                for line in result.stdout.strip().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        wpa[k] = v
                if wpa.get("wpa_state") == "COMPLETED":
                    new_ip = wpa.get("ip_address", "")
                    connected = True
                    break

            if connected:
                # Re-enable all networks and save
                wpa_cli(wifi_iface, "enable_network", "all")
                wpa_cli(wifi_iface, "save_config")
                with wifi_connect_lock:
                    wifi_connect_status.update({
                        "status": "success",
                        "message": f"Connected to {ssid}",
                        "ip": new_ip,
                    })
            else:
                # Restore backup config
                if backup_conf is not None:
                    try:
                        Path(conf_path).write_text(backup_conf)
                        wpa_cli(wifi_iface, "reconfigure")
                    except Exception:
                        pass
                with wifi_connect_lock:
                    wifi_connect_status.update({
                        "status": "failed",
                        "message": f"Failed to connect to {ssid}",
                        "ip": "",
                    })
        except Exception as e:
            with wifi_connect_lock:
                wifi_connect_status.update({
                    "status": "failed",
                    "message": str(e),
                    "ip": "",
                })

    threading.Thread(target=do_connect, daemon=True).start()
    return _json_response(status="connecting", data={"status": "connecting"})


@app.route("/box/api/wifi/connect/status")
@login_required
def api_wifi_connect_status():
    with wifi_connect_lock:
        payload = dict(wifi_connect_status)
        return _json_response(data=payload, **payload)


# ── Tunnel Endpoints ────────────────────────────────────────────

@app.route("/box/api/tunnel/status")
@login_required
def api_tunnel_status():
    client_id, state = _get_or_create_tunnel_client_id()
    payload = _build_tunnel_status_payload(client_id, state)
    _schedule_tunnel_state_refresh(client_id)
    return _json_response(data=payload, **payload)


@app.route("/box/api/tunnel/create-invoice", methods=["POST"])
@login_required
def api_tunnel_create_invoice():
    data = request.get_json(silent=True) or {}
    days = int(data.get("days") or 0)
    if days <= 0:
        return _json_error("Days must be greater than zero", 400)

    client_id, state = _get_or_create_tunnel_client_id()
    state = _sync_tunnel_state_from_remote(state, client_id)
    action = choose_invoice_action(state.get("current_tunnel"))
    if action != "create":
        return _json_error("Tunnel already exists. Use renewal.", 409)

    if DEV_MODE:
        now_iso = datetime.now().isoformat()
        tunnel = {
            "tunnel_id": "dev-tunnel-id",
            "subdomain": "devtunnel",
            "remote_port": 10005,
            "ssh_user": TUNNEL_SSH_USER_FALLBACK,
            "ssh_host": TUNNEL_SSH_HOST_FALLBACK,
            "public_url": "https://devtunnel.lnpro.xyz",
            "expires_at": now_iso,
            "status": "pending",
            "client_note": client_id,
        }
        _write_key_file("-----BEGIN OPENSSH PRIVATE KEY-----\nDEV\n-----END OPENSSH PRIVATE KEY-----\n")
        state["current_tunnel"] = tunnel
        state["pending_invoice"] = {
            "action": "create",
            "tunnel_id": tunnel["tunnel_id"],
            "days": days,
            "payment_hash": "dev-payment-hash",
            "payment_request": "lnbc1devinvoice",
            "created_at": now_iso,
            "baseline_expires_at": tunnel.get("expires_at"),
        }
        _save_tunnel_state(state)
        payload = {
            "invoice": state["pending_invoice"],
            "current_tunnel": tunnel,
            "connect_script": _tunnel_connect_script(tunnel),
        }
        return _json_response(status="ok", data=payload, **payload)

    try:
        resp = _lnpro_request("POST", "tunnels", {
            "public_id": TUNNEL_PUBLIC_ID,
            "days": days,
            "client_note": client_id,
        })
        if not resp.ok:
            return _json_error(f"lnpro API error ({resp.status_code})", 502)
        payload = resp.json()
        if not payload.get("tunnel_id") or not payload.get("payment_request"):
            return _json_error("Invalid lnpro response", 502)

        tunnel = _normalize_tunnel(payload)
        tunnel["status"] = "pending"
        private_key = payload.get("ssh_private_key") or ""
        if not private_key:
            return _json_error("Missing SSH private key in lnpro response", 502)

        _write_key_file(private_key)
        state["current_tunnel"] = tunnel
        state["pending_invoice"] = {
            "action": "create",
            "tunnel_id": payload.get("tunnel_id"),
            "days": days,
            "payment_hash": payload.get("payment_hash"),
            "payment_request": payload.get("payment_request"),
            "created_at": datetime.now().isoformat(),
            "baseline_expires_at": payload.get("expires_at"),
        }
        _save_tunnel_state(state)
        response_payload = {
            "invoice": state["pending_invoice"],
            "current_tunnel": tunnel,
            "connect_script": _tunnel_connect_script(tunnel),
        }
        return _json_response(status="ok", data=response_payload, **response_payload)
    except Exception as e:
        return _json_error(str(e), 500)


@app.route("/box/api/tunnel/renew-invoice", methods=["POST"])
@login_required
def api_tunnel_renew_invoice():
    data = request.get_json(silent=True) or {}
    days = int(data.get("days") or 0)
    if days <= 0:
        return _json_error("Days must be greater than zero", 400)

    client_id, state = _get_or_create_tunnel_client_id()
    state = _sync_tunnel_state_from_remote(state, client_id)
    current = state.get("current_tunnel") or {}
    tunnel_id = current.get("tunnel_id")
    if not tunnel_id:
        return _json_error("No existing tunnel found to renew", 404)

    if DEV_MODE:
        state["pending_invoice"] = {
            "action": "renew",
            "tunnel_id": tunnel_id,
            "days": days,
            "payment_hash": "dev-topup-hash",
            "payment_request": "lnbc1devtopup",
            "created_at": datetime.now().isoformat(),
            "baseline_expires_at": current.get("expires_at"),
        }
        _save_tunnel_state(state)
        payload = {
            "invoice": state["pending_invoice"],
            "current_tunnel": current,
            "connect_script": _tunnel_connect_script(current),
        }
        return _json_response(status="ok", data=payload, **payload)

    try:
        resp = _lnpro_request("PUT", f"payments/public/{tunnel_id}", {"days": days})
        if not resp.ok:
            return _json_error(f"lnpro API error ({resp.status_code})", 502)
        payload = resp.json()
        if not payload.get("payment_request"):
            return _json_error("Invalid renewal response", 502)

        state["pending_invoice"] = {
            "action": "renew",
            "tunnel_id": tunnel_id,
            "days": days,
            "payment_hash": payload.get("payment_hash"),
            "payment_request": payload.get("payment_request"),
            "created_at": datetime.now().isoformat(),
            "baseline_expires_at": current.get("expires_at"),
        }
        _save_tunnel_state(state)
        response_payload = {
            "invoice": state["pending_invoice"],
            "current_tunnel": current,
            "connect_script": _tunnel_connect_script(current),
        }
        return _json_response(status="ok", data=response_payload, **response_payload)
    except Exception as e:
        return _json_error(str(e), 500)


@app.route("/box/api/tunnel/poll", methods=["POST"])
@login_required
def api_tunnel_poll():
    client_id, state = _get_or_create_tunnel_client_id()
    state = _sync_tunnel_state_from_remote(state, client_id)
    current = state.get("current_tunnel")
    pending = state.get("pending_invoice")

    if DEV_MODE and pending and pending.get("action") == "renew":
        # Simple mock progression for local UI development
        current = current or {}
        current["status"] = "active"
        state["current_tunnel"] = current

    paid = pending is None
    if pending and current and is_pending_invoice_paid(pending, current):
        state["pending_invoice"] = None
        _save_tunnel_state(state)
        pending = None
        paid = True

    payload = {
        "paid": paid,
        "client_id": client_id,
        "current_tunnel": state.get("current_tunnel"),
        "pending_invoice": pending,
        "service_status": _tunnel_service_status(),
        "connect_script": _tunnel_connect_script(state.get("current_tunnel")),
    }
    return _json_response(status="ok", data=payload, **payload)


@app.route("/box/api/tunnel/start", methods=["POST"])
@login_required
def api_tunnel_start():
    client_id, state = _get_or_create_tunnel_client_id()
    state = _sync_tunnel_state_from_remote(state, client_id)
    current = state.get("current_tunnel") or {}
    pending = state.get("pending_invoice")

    if not current.get("tunnel_id"):
        return jsonify({"status": "error", "message": "No tunnel configured"}), 404
    if pending:
        return jsonify({"status": "error", "message": "Tunnel invoice is still unpaid"}), 409
    if not current.get("remote_port"):
        return jsonify({"status": "error", "message": "Tunnel remote port missing"}), 400
    if not TUNNEL_KEY_FILE.exists():
        return jsonify({"status": "error", "message": "Tunnel key not found. Create tunnel again."}), 400

    if DEV_MODE:
        return jsonify({"status": "ok", "message": "DEV MODE: would start tunnel service"})

    try:
        _write_runtime_env(current)
        subprocess.run(
            ["systemctl", "enable", f"{TUNNEL_SERVICE_NAME}.service"],
            check=True, capture_output=True, timeout=20
        )
        subprocess.run(
            ["systemctl", "restart", f"{TUNNEL_SERVICE_NAME}.service"],
            check=True, capture_output=True, timeout=20
        )
        return jsonify({"status": "ok", "message": "Tunnel service restarted"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr.decode()}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/box/api/tunnel/stop", methods=["POST"])
@login_required
def api_tunnel_stop():
    if DEV_MODE:
        return jsonify({"status": "ok", "message": "DEV MODE: would stop tunnel service"})

    try:
        subprocess.run(
            ["systemctl", "stop", f"{TUNNEL_SERVICE_NAME}.service"],
            check=True, capture_output=True, timeout=20
        )
        return jsonify({"status": "ok", "message": "Tunnel service stopped"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr.decode()}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/box/api/qrcode", methods=["POST"])
@login_required
def api_qrcode():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return _json_error("QR payload is required", 400)
    if len(text) > 4096:
        return _json_error("QR payload is too large", 400)

    try:
        import qrcode

        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(text)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        response = send_file(image_bytes, mimetype="image/png")
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as e:
        return _json_error(str(e), 500)


# ── OTA Update Endpoints ─────────────────────────────────────────

def get_current_version():
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "dev"


@app.route("/box/api/update/check")
@login_required
def api_update_check():
    if DEV_MODE:
        payload = {
            "current_version": "1.0.0",
            "latest_version": "1.1.0",
            "update_available": True,
            "release_notes": "DEV MODE: Mock update available.\n- Bug fixes\n- Performance improvements",
            "release_tag": "v1.1.0",
        }
        return _json_response(data=payload, **payload)

    current = get_current_version()
    try:
        import requests
        resp = requests.get(GITHUB_RELEASES_URL, timeout=10, headers={
            "Accept": "application/vnd.github.v3+json",
        })
        if not resp.ok:
            return _json_error("Failed to check for updates", 502, upstream_status_code=resp.status_code)

        release = resp.json()
        latest_tag = release.get("tag_name", "")
        latest_version = latest_tag.lstrip("v")
        release_notes = release.get("body", "")

        has_manifest = any(
            a.get("name") == "manifest.json"
            for a in release.get("assets", [])
        )

        payload = {
            "current_version": current,
            "latest_version": latest_version,
            "update_available": latest_version != current and has_manifest,
            "release_notes": release_notes,
            "release_tag": latest_tag,
        }
        return _json_response(data=payload, **payload)
    except Exception as e:
        return _json_error(str(e), 500)


@app.route("/box/api/update/start", methods=["POST"])
@login_required
def api_update_start():
    if DEV_MODE:
        return jsonify({"status": "started", "message": "DEV MODE: would start update"})

    # Check if an update is already in progress
    status_file = UPDATE_STATE_DIR / "status"
    try:
        current_status = status_file.read_text().strip()
        if current_status in ("downloading", "activating"):
            return jsonify({"status": "error", "message": "Update already in progress"}), 409
    except Exception:
        pass

    data = request.get_json(silent=True) or {}
    release_tag = data.get("release_tag", "")
    if not release_tag:
        return jsonify({"status": "error", "message": "No release_tag provided"}), 400

    # Reset status to idle before starting
    try:
        UPDATE_STATE_DIR.mkdir(parents=True, exist_ok=True)
        (UPDATE_STATE_DIR / "status").write_text("idle")
        (UPDATE_STATE_DIR / "log").write_text("")
    except Exception:
        pass

    # Launch update as a transient systemd unit so it survives admin app restarts
    try:
        result = subprocess.run(
            [
                "systemd-run",
                "--system",
                "--unit=lnbitsbox-update",
                "--description=LNbitsBox OTA Update",
                "--setenv=PATH=/run/current-system/sw/bin:/usr/bin:/bin",
                "--no-block",
                "/run/current-system/sw/bin/lnbitsbox-update", release_tag,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            app.logger.error("systemd-run failed: %s", result.stderr.strip())
            return jsonify({"status": "error", "message": result.stderr.strip()}), 500
        return jsonify({"status": "started"})
    except Exception as e:
        app.logger.error("Failed to launch update: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/box/api/update/status")
@login_required
def api_update_status():
    if DEV_MODE:
        payload = {
            "status": "idle",
            "log_lines": ["DEV MODE: No update in progress"],
            "target_version": "",
        }
        return _json_response(data=payload, **payload)

    status = "idle"
    log_lines = []
    target_version = ""

    try:
        status = (UPDATE_STATE_DIR / "status").read_text().strip()
    except Exception:
        pass

    try:
        log_text = (UPDATE_STATE_DIR / "log").read_text()
        log_lines = log_text.strip().splitlines()[-50:]  # Last 50 lines
    except Exception:
        pass

    try:
        target_version = (UPDATE_STATE_DIR / "target-version").read_text().strip()
    except Exception:
        pass

    payload = {
        "status": status,
        "log_lines": log_lines,
        "target_version": target_version,
    }
    return _json_response(data=payload, **payload)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8090, debug=DEV_MODE)
