import io
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from recovery_utils import (
        available_restore_components,
        build_backup_manifest,
        compatibility_report,
        file_sha256,
        load_backup_container,
        package_encrypted_backup,
        package_plain_backup,
        select_scheduled_backups_to_keep,
        validate_manifest_files,
    )
    RECOVERY_IMPORT_ERROR = None
except ModuleNotFoundError as exc:  # pragma: no cover - local env only
    RECOVERY_IMPORT_ERROR = exc


class RecoveryUtilsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if RECOVERY_IMPORT_ERROR is not None:
            raise unittest.SkipTest(f"recovery_utils dependencies unavailable: {RECOVERY_IMPORT_ERROR}")

    def _component_payloads(self):
        payload = b"hello backup"
        return {
            "database": [
                {
                    "archive_path": "database/database.sqlite3",
                    "destination_path": "/var/lib/lnbits/database.sqlite3",
                    "content": payload,
                    "size": len(payload),
                    "sha256": file_sha256(payload),
                    "mode": "0o640",
                }
            ]
        }

    def test_plain_backup_round_trip(self):
        payloads = self._component_payloads()
        manifest = build_backup_manifest(
            backup_type="full",
            current_version="0.1.49",
            encrypted=False,
            components=payloads,
            spark_seed_present=True,
            tunnel_configured=False,
        )
        archive = package_plain_backup(manifest, payloads)
        loaded_manifest, inner_zip = load_backup_container(archive)
        self.assertEqual(loaded_manifest["backup_type"], "full")
        self.assertEqual(loaded_manifest["created_by"], "manual")
        self.assertEqual(validate_manifest_files(loaded_manifest, inner_zip), [])
        self.assertIn("database", available_restore_components(loaded_manifest))

    def test_encrypted_backup_requires_password(self):
        payloads = self._component_payloads()
        manifest = build_backup_manifest(
            backup_type="full",
            current_version="0.1.49",
            encrypted=True,
            components=payloads,
            spark_seed_present=True,
            tunnel_configured=True,
        )
        plain_archive = package_plain_backup(manifest, payloads)
        encrypted_archive = package_encrypted_backup(manifest, plain_archive, "correct horse battery staple")

        with self.assertRaises(ValueError):
            load_backup_container(encrypted_archive)

        with self.assertRaises(ValueError):
            load_backup_container(encrypted_archive, passphrase="wrong")

        loaded_manifest, inner_zip = load_backup_container(
            encrypted_archive,
            passphrase="correct horse battery staple",
        )
        self.assertTrue(loaded_manifest["encrypted"])
        self.assertEqual(validate_manifest_files(loaded_manifest, inner_zip), [])

    def test_validate_manifest_catches_missing_file(self):
        payloads = self._component_payloads()
        manifest = build_backup_manifest(
            backup_type="quick",
            current_version="0.1.49",
            encrypted=False,
            components=payloads,
            spark_seed_present=False,
            tunnel_configured=False,
        )
        broken_archive = io.BytesIO()
        with zipfile.ZipFile(broken_archive, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", "{}")
        with zipfile.ZipFile(io.BytesIO(broken_archive.getvalue()), "r") as zf:
            issues = validate_manifest_files(manifest, zf)
        self.assertTrue(issues)

    def test_compatibility_report(self):
        self.assertEqual(compatibility_report("0.1.49", "0.1.50")["level"], "ok")
        self.assertEqual(compatibility_report("0.2.0", "0.1.49")["level"], "warn")
        self.assertEqual(compatibility_report("1.0.0", "0.1.49")["level"], "error")

    def test_scheduled_backup_retention_keeps_recent_daily_and_weekly_windows(self):
        now = datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)
        backups = [
            (Path("/tmp/hourly-1.zip"), now - timedelta(hours=1)),
            (Path("/tmp/hourly-20.zip"), now - timedelta(hours=20)),
            (Path("/tmp/day-2-new.zip"), now - timedelta(days=2, hours=1)),
            (Path("/tmp/day-2-old.zip"), now - timedelta(days=2, hours=6)),
            (Path("/tmp/day-6.zip"), now - timedelta(days=6, hours=2)),
            (Path("/tmp/week-2-new.zip"), now - timedelta(days=10, hours=1)),
            (Path("/tmp/week-2-old.zip"), now - timedelta(days=12)),
            (Path("/tmp/week-4.zip"), now - timedelta(days=24)),
            (Path("/tmp/older-than-window.zip"), now - timedelta(days=40)),
        ]

        keep = select_scheduled_backups_to_keep(backups, now=now)

        self.assertIn(Path("/tmp/hourly-1.zip"), keep)
        self.assertIn(Path("/tmp/hourly-20.zip"), keep)
        self.assertIn(Path("/tmp/day-2-new.zip"), keep)
        self.assertNotIn(Path("/tmp/day-2-old.zip"), keep)
        self.assertIn(Path("/tmp/day-6.zip"), keep)
        self.assertIn(Path("/tmp/week-2-new.zip"), keep)
        self.assertNotIn(Path("/tmp/week-2-old.zip"), keep)
        self.assertIn(Path("/tmp/week-4.zip"), keep)
        self.assertNotIn(Path("/tmp/older-than-window.zip"), keep)

    def test_scheduled_backup_retention_keeps_latest_even_when_outside_windows(self):
        now = datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)
        backups = [
            (Path("/tmp/latest-old.zip"), now - timedelta(days=60)),
            (Path("/tmp/older.zip"), now - timedelta(days=90)),
        ]

        keep = select_scheduled_backups_to_keep(backups, now=now)

        self.assertEqual(keep, {Path("/tmp/latest-old.zip")})


if __name__ == "__main__":
    unittest.main()
