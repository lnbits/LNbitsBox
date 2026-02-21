#!/usr/bin/env python3
"""LNbitsBox Admin Dashboard — system monitoring and service management"""

import json
import os
import sys
import time
try:
    import crypt
except ModuleNotFoundError:
    crypt = None  # Removed in Python 3.13; only needed on NixOS Pi
import shutil
import subprocess
import threading
from collections import deque
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)

app = Flask(__name__, static_url_path="/box/static")
app.secret_key = os.urandom(24)

# Configuration
DEV_MODE = os.environ.get("DEV_MODE", "false") == "true"
SSH_USER = "lnbitsadmin"
SPARK_URL = os.environ.get("SPARK_URL", "http://127.0.0.1:8765")
try:
    SPARK_SIDECAR_API_KEY = Path("/var/lib/spark-sidecar/api-key.env").read_text().strip().split("=")[1]
except Exception:
    SPARK_SIDECAR_API_KEY = ""
LNBITS_URL = os.environ.get("LNBITS_URL", "http://127.0.0.1:5000")
ALLOWED_SERVICES = ["lnbits", "spark-sidecar"]
UPDATE_STATE_DIR = Path("/var/lib/lnbitsbox-update")
VERSION_FILE = Path("/etc/lnbitsbox-version")
GITHUB_RELEASES_URL = "https://api.github.com/repos/lnbits/LNbitsBox/releases/latest"

# Stats history — 2 hours at 30s intervals = 240 data points
STATS_INTERVAL = 30
STATS_HISTORY_SIZE = 240
stats_history = deque(maxlen=STATS_HISTORY_SIZE)
stats_lock = threading.Lock()

# WiFi connection state
wifi_connect_status = {"status": "idle", "message": "", "ip": ""}
wifi_connect_lock = threading.Lock()


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


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/box/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        password = request.form.get("password", "")

        if authenticate(SSH_USER, password):
            session["authenticated"] = True
            return redirect(url_for("dashboard"))

        flash("Invalid password", "error")

    return render_template("login.html")


@app.route("/box/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/box/")
@login_required
def dashboard():
    return render_template("dashboard.html", dev_mode=DEV_MODE)


@app.route("/box/api/stats")
@login_required
def api_stats():
    current = collect_stats()
    with stats_lock:
        history = list(stats_history)
    return jsonify({
        "current": current,
        "history": {
            "timestamps": [s["timestamp"] for s in history],
            "cpu": [s["cpu_percent"] for s in history],
            "ram": [s["ram"]["percent"] for s in history],
            "temp": [s["cpu_temp"] for s in history],
        }
    })


@app.route("/box/api/lnbits-status")
@login_required
def api_lnbits_status():
    code = get_lnbits_http_status()
    if code == 200:
        return jsonify({"status": "running"})
    elif code == 502:
        return jsonify({"status": "starting"})
    elif code is not None:
        return jsonify({"status": "error", "code": code})
    else:
        return jsonify({"status": "stopped"})


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
    if service not in ALLOWED_SERVICES:
        return jsonify({"status": "error", "message": "Invalid service"}), 400

    if DEV_MODE:
        return jsonify({"status": "ok", "message": f"DEV MODE: would restart {service}"})

    try:
        subprocess.run(
            ["systemctl", "restart", f"{service}.service"],
            check=True, capture_output=True, timeout=30
        )
        return jsonify({"status": "ok", "message": f"{service} restarted"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr.decode()}), 500


# ── WiFi Endpoints ──────────────────────────────────────────────

@app.route("/box/api/wifi/scan", methods=["POST"])
@login_required
def api_wifi_scan():
    if DEV_MODE:
        return jsonify({"networks": [
            {"ssid": "HomeNetwork", "signal": -45, "flags": "[WPA2-PSK-CCMP][ESS]"},
            {"ssid": "CoffeeShop_Free", "signal": -62, "flags": "[ESS]"},
            {"ssid": "Neighbor5G", "signal": -70, "flags": "[WPA2-PSK-CCMP][WPS][ESS]"},
            {"ssid": "OfficeWiFi", "signal": -78, "flags": "[WPA2-EAP-CCMP][ESS]"},
        ]})

    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return jsonify({"error": "No wireless interface found"}), 404

    try:
        wpa_cli(wifi_iface, "scan")
        time.sleep(3)
        result = wpa_cli(wifi_iface, "scan_results")
        if result.returncode != 0:
            return jsonify({"error": "Scan failed"}), 500

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
        return jsonify({"networks": sorted_networks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/box/api/wifi/connect", methods=["POST"])
@login_required
def api_wifi_connect():
    data = request.get_json(silent=True) or {}
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "")

    if not ssid:
        return jsonify({"status": "error", "message": "SSID is required"}), 400

    if DEV_MODE:
        with wifi_connect_lock:
            wifi_connect_status.update({"status": "connecting", "message": f"Connecting to {ssid}...", "ip": ""})

        def mock_connect():
            time.sleep(4)
            with wifi_connect_lock:
                wifi_connect_status.update({"status": "success", "message": f"Connected to {ssid}", "ip": "192.168.1.42"})
        threading.Thread(target=mock_connect, daemon=True).start()
        return jsonify({"status": "connecting"})

    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return jsonify({"status": "error", "message": "No wireless interface found"}), 404

    with wifi_connect_lock:
        if wifi_connect_status["status"] == "connecting":
            return jsonify({"status": "error", "message": "Connection attempt already in progress"}), 409
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
    return jsonify({"status": "connecting"})


@app.route("/box/api/wifi/connect/status")
@login_required
def api_wifi_connect_status():
    with wifi_connect_lock:
        return jsonify(dict(wifi_connect_status))


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
        return jsonify({
            "current_version": "1.0.0",
            "latest_version": "1.1.0",
            "update_available": True,
            "release_notes": "DEV MODE: Mock update available.\n- Bug fixes\n- Performance improvements",
            "release_tag": "v1.1.0",
        })

    current = get_current_version()
    try:
        import requests
        resp = requests.get(GITHUB_RELEASES_URL, timeout=10, headers={
            "Accept": "application/vnd.github.v3+json",
        })
        if not resp.ok:
            return jsonify({"error": "Failed to check for updates", "status_code": resp.status_code}), 502

        release = resp.json()
        latest_tag = release.get("tag_name", "")
        latest_version = latest_tag.lstrip("v")
        release_notes = release.get("body", "")

        has_manifest = any(
            a.get("name") == "manifest.json"
            for a in release.get("assets", [])
        )

        return jsonify({
            "current_version": current,
            "latest_version": latest_version,
            "update_available": latest_version != current and has_manifest,
            "release_notes": release_notes,
            "release_tag": latest_tag,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        return jsonify({
            "status": "idle",
            "log_lines": ["DEV MODE: No update in progress"],
            "target_version": "",
        })

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

    return jsonify({
        "status": status,
        "log_lines": log_lines,
        "target_version": target_version,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8090, debug=DEV_MODE)
