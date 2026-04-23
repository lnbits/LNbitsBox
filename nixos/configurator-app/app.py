#!/usr/bin/env python3
"""
LNbitsBox First-Run Configuration Wizard
Handles funding source selection, mnemonic generation/import, and SSH password setup
"""

import os
import sys
import secrets
import subprocess
import grp
import pwd
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from mnemonic import Mnemonic

app = Flask(__name__)
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)

# Development mode - use /tmp paths instead of system paths
DEV_MODE = os.environ.get("DEV_MODE", "false") == "true"

if DEV_MODE:
    MARKER_FILE = Path("/tmp/lnbitspi-test/lnbits/.configured")
    SPARK_MNEMONIC_FILE = Path("/tmp/lnbitspi-test/spark-sidecar/mnemonic")
    PHOENIXD_STATE_DIR = Path("/tmp/lnbitspi-test/phoenixd/.phoenix")
    ENV_FILE = Path("/tmp/lnbitspi-test/lnbits-config/lnbits.env")
    SPARK_SIDECAR_ENV_FILE = Path("/tmp/lnbitspi-test/spark-sidecar/api-key.env")
    FUNDING_SOURCE_FILE = Path("/tmp/lnbitspi-test/lnbitsbox/funding-source")
    SSH_USER = os.environ.get("USER")  # Use current user instead of lnbitsadmin
else:
    MARKER_FILE = Path("/var/lib/lnbits/.configured")
    SPARK_MNEMONIC_FILE = Path("/var/lib/spark-sidecar/mnemonic")
    PHOENIXD_STATE_DIR = Path("/var/lib/phoenixd/.phoenix")
    ENV_FILE = Path("/etc/lnbits/lnbits.env")
    SPARK_SIDECAR_ENV_FILE = Path("/var/lib/spark-sidecar/api-key.env")
    FUNDING_SOURCE_FILE = Path("/var/lib/lnbitsbox/funding-source")
    SSH_USER = "lnbitsadmin"

PHOENIXD_SEED_FILE = PHOENIXD_STATE_DIR / "seed.dat"
PHOENIXD_CONF_FILE = PHOENIXD_STATE_DIR / "phoenix.conf"
FUNDING_SOURCES = {
    "spark": {
        "label": "Spark",
        "seed_label": "Spark Wallet Seed",
        "secret_owner": "spark-sidecar",
        "seed_file": SPARK_MNEMONIC_FILE,
        "service": "spark-sidecar.service",
    },
    "phoenixd": {
        "label": "Phoenixd",
        "seed_label": "Phoenixd Wallet Seed",
        "secret_owner": "phoenixd",
        "seed_file": PHOENIXD_SEED_FILE,
        "service": "phoenixd.service",
    },
}

# In-memory state for wizard (cleared after completion)
wizard_state = {}


def is_configured():
    """Check if system has been configured"""
    return MARKER_FILE.exists()


def selected_funding_source():
    source = wizard_state.get("funding_source", "spark")
    return source if source in FUNDING_SOURCES else "spark"


def funding_source_info():
    source = selected_funding_source()
    return {"key": source, **FUNDING_SOURCES[source]}


def normalize_mnemonic(value: str) -> str:
    return " ".join(value.strip().lower().split())


def read_key_value_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return values


def chown_if_user_exists(path: Path, user: str, group: str | None = None):
    try:
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(group or user).gr_gid
        os.chown(path, uid, gid)
    except KeyError:
        pass


def chgrp_if_group_exists(path: Path, group: str):
    try:
        gid = grp.getgrnam(group).gr_gid
        os.chown(path, 0, gid)
    except KeyError:
        pass


def ensure_phoenixd_config():
    PHOENIXD_STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o750)
    PHOENIXD_STATE_DIR.parent.chmod(0o750)
    PHOENIXD_STATE_DIR.chmod(0o750)
    chown_if_user_exists(PHOENIXD_STATE_DIR.parent, "phoenixd")
    chown_if_user_exists(PHOENIXD_STATE_DIR, "phoenixd")
    if not PHOENIXD_CONF_FILE.exists():
        PHOENIXD_CONF_FILE.write_text(
            "\n".join([
                "chain=mainnet",
                "http-bind-address=127.0.0.1",
                "http-bind-port=9740",
                "auto-liquidity=2m",
                f"http-password={secrets.token_hex(32)}",
                "",
            ])
        )
        PHOENIXD_CONF_FILE.chmod(0o640)
    chown_if_user_exists(PHOENIXD_CONF_FILE, "phoenixd")
    PHOENIXD_CONF_FILE.chmod(0o640)


@app.route("/")
def index():
    """Welcome page"""
    if is_configured():
        return render_template("already_configured.html")
    return render_template("index.html")


@app.route("/funding-source", methods=["GET", "POST"])
def funding_source():
    """Select the LNbits backend wallet / funding source"""
    if is_configured():
        return redirect(url_for("index"))

    if request.method == "POST":
        source = request.form.get("funding_source", "spark")
        if source not in FUNDING_SOURCES:
            flash("Please choose a valid funding source", "error")
            return render_template("funding_source.html", selected=selected_funding_source())
        wizard_state["funding_source"] = source
        return redirect(url_for("seed"))

    return render_template("funding_source.html", selected=selected_funding_source())


@app.route("/seed", methods=["GET", "POST"])
def seed():
    """Generate or import BIP39 mnemonic"""
    if is_configured():
        return redirect(url_for("index"))

    if "funding_source" not in wizard_state:
        return redirect(url_for("funding_source"))

    source_info = funding_source_info()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "generate":
            # Generate 12-word BIP39 mnemonic
            mnemo = Mnemonic("english")
            mnemonic = mnemo.generate(strength=128)  # 128 bits = 12 words
            wizard_state["mnemonic"] = mnemonic
            wizard_state["mnemonic_confirmed"] = False
            return render_template("seed.html", mnemonic=mnemonic, action="display", funding_source=source_info)

        elif action == "confirm":
            # User confirmed they saved the mnemonic
            confirmed = request.form.get("confirmed")
            if confirmed == "yes":
                wizard_state["mnemonic_confirmed"] = True
                return redirect(url_for("password"))
            else:
                flash("Please confirm you have saved the seed phrase", "error")
                mnemonic = wizard_state.get("mnemonic")
                return render_template("seed.html", mnemonic=mnemonic, action="display", funding_source=source_info)

        elif action == "import":
            # Import existing mnemonic
            imported_mnemonic = normalize_mnemonic(request.form.get("mnemonic", ""))
            mnemo = Mnemonic("english")

            if not imported_mnemonic:
                flash("Please enter a mnemonic", "error")
                return render_template("seed.html", action="choose", funding_source=source_info)

            # Validate mnemonic
            if not mnemo.check(imported_mnemonic):
                flash("Invalid mnemonic. Please check and try again.", "error")
                return render_template("seed.html", action="choose", funding_source=source_info)

            wizard_state["mnemonic"] = imported_mnemonic
            wizard_state["mnemonic_confirmed"] = True
            return redirect(url_for("password"))

    # GET request
    return render_template("seed.html", action="choose", funding_source=source_info)


@app.route("/password", methods=["GET", "POST"])
def password():
    """Set SSH password for lnbitsadmin user"""
    if is_configured():
        return redirect(url_for("index"))

    if "funding_source" not in wizard_state:
        flash("Please choose a funding source first", "error")
        return redirect(url_for("funding_source"))

    if "mnemonic" not in wizard_state or not wizard_state.get("mnemonic_confirmed"):
        flash("Please complete the seed setup first", "error")
        return redirect(url_for("seed"))

    if request.method == "POST":
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")

        # Validation
        if not password1:
            flash("Please enter a password", "error")
            return render_template("password.html")

        if len(password1) < 8:
            flash("Password must be at least 8 characters", "error")
            return render_template("password.html")

        if password1 != password2:
            flash("Passwords do not match", "error")
            return render_template("password.html")

        # Set password using chpasswd (secure, no shell exposure)
        try:
            chpasswd_input = f"{SSH_USER}:{password1}"
            if DEV_MODE:
                print(f"[DEV MODE] Would set password for user: {SSH_USER}")
                # In dev mode, just log it instead of actually setting
            else:
                subprocess.run(
                    ["chpasswd"],
                    input=chpasswd_input.encode(),
                    check=True,
                    capture_output=True
                )
            wizard_state["password_set"] = True
            return redirect(url_for("complete"))
        except subprocess.CalledProcessError as e:
            flash(f"Failed to set password: {e.stderr.decode()}", "error")
            return render_template("password.html")

    return render_template("password.html")


@app.route("/complete")
def complete():
    """Finalize setup: write files, create marker, start services"""
    if is_configured():
        return redirect(url_for("index"))

    if "funding_source" not in wizard_state or "mnemonic" not in wizard_state or not wizard_state.get("password_set"):
        flash("Please complete all setup steps", "error")
        return redirect(url_for("index"))

    try:
        source = selected_funding_source()
        source_info = FUNDING_SOURCES[source]
        mnemonic_file = source_info["seed_file"]
        service_name = source_info["service"]

        if source == "phoenixd":
            ensure_phoenixd_config()

        # 1. Create funding source state directory if needed
        mnemonic_file.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
        if source == "phoenixd":
            chown_if_user_exists(mnemonic_file.parent, "phoenixd")
        else:
            chgrp_if_group_exists(mnemonic_file.parent, "spark-sidecar")

        # 2. Write mnemonic file with correct permissions
        mnemonic = normalize_mnemonic(wizard_state["mnemonic"])
        mnemonic_file.write_text(mnemonic + "\n")
        mnemonic_file.chmod(0o640)

        # Set ownership to the selected funding source service.
        if source == "phoenixd":
            chown_if_user_exists(mnemonic_file, "phoenixd")
        else:
            chgrp_if_group_exists(mnemonic_file, source_info["secret_owner"])

        # 3. Update LNbits env file with selected funding source configuration
        FUNDING_SOURCE_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        FUNDING_SOURCE_FILE.write_text(source + "\n")
        FUNDING_SOURCE_FILE.chmod(0o644)
        update_lnbits_env(source)

        # 4. Clear wizard state (security)
        wizard_state.clear()

        # 5. Delay marker creation and service start so the complete page
        #    and its assets are served by the configurator before Caddy
        #    switches routing to LNbits
        def finalize():
            time.sleep(1)
            MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
            MARKER_FILE.touch(mode=0o644)
            if DEV_MODE:
                print(f"[DEV MODE] Would start services: {service_name}, lnbits")
            else:
                subprocess.run(["systemctl", "stop", "spark-sidecar.service"], check=False)
                subprocess.run(["systemctl", "stop", "phoenixd.service"], check=False)
                subprocess.run(["systemctl", "start", service_name], check=False)
                subprocess.run(["systemctl", "start", "lnbits.service"], check=False)
                subprocess.run(["systemctl", "start", "lnbitspi-admin.service"], check=False)
                subprocess.run(["systemctl", "reload", "caddy.service"], check=False)

        threading.Thread(target=finalize, daemon=True).start()

        return render_template("complete.html")

    except Exception as e:
        flash(f"Setup failed: {str(e)}", "error")
        return render_template("error.html", error=str(e))


def update_lnbits_env(source: str):
    """Update /etc/lnbits/lnbits.env with the selected funding source."""
    existing_lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    funding_keys = {
        "LNBITS_BACKEND_WALLET_CLASS",
        "SPARK_L2_EXTERNAL_ENDPOINT",
        "SPARK_L2_EXTERNAL_API_KEY",
        "PHOENIXD_API_ENDPOINT",
        "PHOENIXD_API_PASSWORD",
    }
    kept = [
        line for line in existing_lines
        if not any(line.startswith(key + "=") for key in funding_keys)
        and not line.startswith("# Funding Source Configuration")
    ]

    if source == "spark":
        api_token = secrets.token_hex(32)
        funding_config = [
            "# Funding Source Configuration",
            "LNBITS_BACKEND_WALLET_CLASS=SparkL2Wallet",
            "SPARK_L2_EXTERNAL_ENDPOINT=http://127.0.0.1:8765",
            f"SPARK_L2_EXTERNAL_API_KEY={api_token}",
        ]

        SPARK_SIDECAR_ENV_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
        SPARK_SIDECAR_ENV_FILE.write_text(f"SPARK_SIDECAR_API_KEY={api_token}\n")
        SPARK_SIDECAR_ENV_FILE.chmod(0o640)
        chgrp_if_group_exists(SPARK_SIDECAR_ENV_FILE, "spark-sidecar")
    elif source == "phoenixd":
        ensure_phoenixd_config()
        phoenixd_password = read_key_value_file(PHOENIXD_CONF_FILE).get("http-password", "")
        if not phoenixd_password:
            raise RuntimeError("Phoenixd API password is not available.")
        funding_config = [
            "# Funding Source Configuration",
            "LNBITS_BACKEND_WALLET_CLASS=PhoenixdWallet",
            "PHOENIXD_API_ENDPOINT=http://127.0.0.1:9740/",
            f"PHOENIXD_API_PASSWORD={phoenixd_password}",
        ]
    else:
        raise ValueError("Invalid funding source")

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    ENV_FILE.write_text("\n".join(kept).rstrip() + "\n\n" + "\n".join(funding_config) + "\n")
    ENV_FILE.chmod(0o640)


@app.route("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "configured": is_configured()}


if __name__ == "__main__":
    # Run on loopback only (Caddy will proxy)
    app.run(host="127.0.0.1", port=8080, debug=False)
