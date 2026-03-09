import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tunnel_utils import (
    choose_invoice_action,
    is_pending_invoice_paid,
    select_canonical_tunnel,
    write_secure_json,
    read_json,
)


class TunnelUtilsTest(unittest.TestCase):
    def test_select_canonical_tunnel_prefers_active(self):
        now = datetime.now(timezone.utc)
        tunnels = [
            {"tunnel_id": "a", "status": "expired", "expires_at": (now + timedelta(days=10)).isoformat()},
            {"tunnel_id": "b", "status": "active", "expires_at": (now + timedelta(days=2)).isoformat()},
            {"tunnel_id": "c", "status": "active", "expires_at": (now + timedelta(days=5)).isoformat()},
        ]
        selected = select_canonical_tunnel(tunnels)
        self.assertEqual(selected["tunnel_id"], "c")

    def test_select_canonical_tunnel_latest_when_no_active(self):
        now = datetime.now(timezone.utc)
        tunnels = [
            {"tunnel_id": "a", "status": "expired", "expires_at": (now + timedelta(days=1)).isoformat()},
            {"tunnel_id": "b", "status": "pending", "expires_at": (now + timedelta(days=3)).isoformat()},
        ]
        selected = select_canonical_tunnel(tunnels)
        self.assertEqual(selected["tunnel_id"], "b")

    def test_choose_invoice_action(self):
        self.assertEqual(choose_invoice_action(None), "create")
        self.assertEqual(choose_invoice_action({}), "create")
        self.assertEqual(choose_invoice_action({"tunnel_id": "x"}), "renew")

    def test_is_pending_invoice_paid_create(self):
        pending = {"action": "create", "tunnel_id": "abc"}
        canonical = {"tunnel_id": "abc", "status": "active"}
        self.assertTrue(is_pending_invoice_paid(pending, canonical))

    def test_is_pending_invoice_paid_renew(self):
        before = datetime.now(timezone.utc)
        after = before + timedelta(days=1)
        pending = {
            "action": "renew",
            "tunnel_id": "abc",
            "baseline_expires_at": before.isoformat(),
        }
        canonical = {
            "tunnel_id": "abc",
            "status": "active",
            "expires_at": after.isoformat(),
        }
        self.assertTrue(is_pending_invoice_paid(pending, canonical))

    def test_write_secure_json_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "state.json"
            write_secure_json(path, {"ok": True}, mode=0o600)
            data = read_json(path)
            self.assertTrue(data["ok"])
            mode = os.stat(path).st_mode & 0o777
            self.assertEqual(mode, 0o600)


if __name__ == "__main__":
    unittest.main()
