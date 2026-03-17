import base64
import hashlib
import io
import json
import secrets
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SCHEMA_VERSION = 1
PBKDF2_ITERATIONS = 390000


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for chunk in (value or "").strip().split("."):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            break
    return tuple(parts)


def compatibility_report(current_version: str, backup_version: str) -> dict[str, str]:
    current = parse_version_tuple(current_version)
    backup = parse_version_tuple(backup_version)
    if not current or not backup:
        return {
            "level": "warn",
            "message": "Version compatibility could not be fully checked.",
        }
    if current[:1] != backup[:1]:
        return {
            "level": "error",
            "message": f"Backup version {backup_version} is from a different major release than this box ({current_version}).",
        }
    if current[:2] != backup[:2]:
        return {
            "level": "warn",
            "message": f"Backup version {backup_version} does not match this box version {current_version}. Restore may require follow-up checks.",
        }
    return {
        "level": "ok",
        "message": f"Backup version {backup_version} is compatible with this box ({current_version}).",
    }


def derive_fernet_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def build_backup_manifest(
    *,
    backup_type: str,
    current_version: str,
    encrypted: bool,
    components: dict[str, list[dict[str, Any]]],
    spark_seed_present: bool,
    tunnel_configured: bool,
) -> dict[str, Any]:
    files = []
    component_names = []
    for component_name, entries in components.items():
        if not entries:
            continue
        component_names.append(component_name)
        for entry in entries:
            files.append({
                "component": component_name,
                "archive_path": entry["archive_path"],
                "destination_path": entry["destination_path"],
                "size": entry["size"],
                "sha256": entry["sha256"],
                "mode": entry.get("mode"),
            })

    return {
        "schema_version": SCHEMA_VERSION,
        "backup_id": secrets.token_hex(8),
        "created_at": utc_now_iso(),
        "backup_type": backup_type,
        "lnbitsbox_version": current_version,
        "encrypted": encrypted,
        "components": component_names,
        "files": files,
        "spark_seed_present": spark_seed_present,
        "tunnel_configured": tunnel_configured,
    }


def package_plain_backup(manifest: dict[str, Any], component_payloads: dict[str, list[dict[str, Any]]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        for entries in component_payloads.values():
            for entry in entries:
                zf.writestr(entry["archive_path"], entry["content"])
    return buffer.getvalue()


def package_encrypted_backup(manifest: dict[str, Any], plain_backup: bytes, passphrase: str) -> bytes:
    salt = secrets.token_bytes(16)
    key = derive_fernet_key(passphrase, salt)
    encrypted_payload = Fernet(key).encrypt(plain_backup)
    outer_buffer = io.BytesIO()
    with zipfile.ZipFile(outer_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        zf.writestr(
            "encryption.json",
            json.dumps(
                {
                    "algorithm": "fernet-pbkdf2-sha256",
                    "salt_b64": base64.b64encode(salt).decode("ascii"),
                    "iterations": PBKDF2_ITERATIONS,
                },
                indent=2,
                sort_keys=True,
            ),
        )
        zf.writestr("backup.enc", encrypted_payload)
    return outer_buffer.getvalue()


def load_backup_container(archive_bytes: bytes, passphrase: str | None = None) -> tuple[dict[str, Any], zipfile.ZipFile]:
    outer_buffer = io.BytesIO(archive_bytes)
    outer_zip = zipfile.ZipFile(outer_buffer, "r")
    manifest = json.loads(outer_zip.read("manifest.json"))
    if not manifest.get("encrypted"):
        plain_buffer = io.BytesIO(archive_bytes)
        return manifest, zipfile.ZipFile(plain_buffer, "r")

    if not passphrase:
        raise ValueError("A passphrase is required to open this backup.")

    encryption_meta = json.loads(outer_zip.read("encryption.json"))
    salt = base64.b64decode(encryption_meta["salt_b64"])
    key = derive_fernet_key(passphrase, salt)
    encrypted_payload = outer_zip.read("backup.enc")
    try:
        plain_backup = Fernet(key).decrypt(encrypted_payload)
    except InvalidToken as exc:
        raise ValueError("Incorrect passphrase for encrypted backup.") from exc

    plain_buffer = io.BytesIO(plain_backup)
    return manifest, zipfile.ZipFile(plain_buffer, "r")


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_manifest_files(manifest: dict[str, Any], inner_zip: zipfile.ZipFile) -> list[str]:
    issues = []
    for file_info in manifest.get("files", []):
        archive_path = file_info.get("archive_path")
        if not archive_path:
            issues.append("Manifest entry is missing archive_path.")
            continue
        try:
            payload = inner_zip.read(archive_path)
        except KeyError:
            issues.append(f"Missing file in archive: {archive_path}")
            continue
        expected_sha = file_info.get("sha256")
        if expected_sha and file_sha256(payload) != expected_sha:
            issues.append(f"Checksum mismatch for {archive_path}")
    return issues


def available_restore_components(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components: dict[str, dict[str, Any]] = {}
    for file_info in manifest.get("files", []):
        component = file_info.get("component") or "unknown"
        item = components.setdefault(component, {"count": 0, "paths": []})
        item["count"] += 1
        item["paths"].append(file_info.get("destination_path"))
    return components


def read_json_file(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json_file(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
