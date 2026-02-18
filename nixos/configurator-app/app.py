#!/usr/bin/env python3
"""
LNbitsBox First-Run Configuration Wizard
Handles Spark mnemonic generation/import and SSH password setup
"""

import os
import sys
import secrets
import subprocess
import grp
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from mnemonic import Mnemonic

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Development mode - use /tmp paths instead of system paths
DEV_MODE = os.environ.get("DEV_MODE", "false") == "true"

if DEV_MODE:
    MARKER_FILE = Path("/tmp/lnbitspi-test/lnbits/.configured")
    MNEMONIC_FILE = Path("/tmp/lnbitspi-test/spark-sidecar/mnemonic")
    ENV_FILE = Path("/tmp/lnbitspi-test/lnbits-config/lnbits.env")
    SPARK_SIDECAR_ENV_FILE = Path("/tmp/lnbitspi-test/spark-sidecar/api-key.env")
    SSH_USER = os.environ.get("USER")  # Use current user instead of lnbitsadmin
else:
    MARKER_FILE = Path("/var/lib/lnbits/.configured")
    MNEMONIC_FILE = Path("/var/lib/spark-sidecar/mnemonic")
    ENV_FILE = Path("/etc/lnbits/lnbits.env")
    SPARK_SIDECAR_ENV_FILE = Path("/var/lib/spark-sidecar/api-key.env")
    SSH_USER = "lnbitsadmin"

# In-memory state for wizard (cleared after completion)
wizard_state = {}


def is_configured():
    """Check if system has been configured"""
    return MARKER_FILE.exists()


@app.route("/")
def index():
    """Welcome page"""
    if is_configured():
        return render_template("already_configured.html")
    return render_template("index.html")


@app.route("/seed", methods=["GET", "POST"])
def seed():
    """Generate or import BIP39 mnemonic"""
    if is_configured():
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "generate":
            # Generate 12-word BIP39 mnemonic
            mnemo = Mnemonic("english")
            mnemonic = mnemo.generate(strength=128)  # 128 bits = 12 words
            wizard_state["mnemonic"] = mnemonic
            wizard_state["mnemonic_confirmed"] = False
            return render_template("seed.html", mnemonic=mnemonic, action="display")

        elif action == "confirm":
            # User confirmed they saved the mnemonic
            confirmed = request.form.get("confirmed")
            if confirmed == "yes":
                wizard_state["mnemonic_confirmed"] = True
                return redirect(url_for("password"))
            else:
                flash("Please confirm you have saved the seed phrase", "error")
                mnemonic = wizard_state.get("mnemonic")
                return render_template("seed.html", mnemonic=mnemonic, action="display")

        elif action == "import":
            # Import existing mnemonic
            imported_mnemonic = request.form.get("mnemonic", "").strip()
            mnemo = Mnemonic("english")

            if not imported_mnemonic:
                flash("Please enter a mnemonic", "error")
                return render_template("seed.html", action="import")

            # Validate mnemonic
            if not mnemo.check(imported_mnemonic):
                flash("Invalid mnemonic. Please check and try again.", "error")
                return render_template("seed.html", action="import")

            wizard_state["mnemonic"] = imported_mnemonic
            wizard_state["mnemonic_confirmed"] = True
            return redirect(url_for("password"))

    # GET request
    return render_template("seed.html", action="choose")


@app.route("/password", methods=["GET", "POST"])
def password():
    """Set SSH password for lnbitsadmin user"""
    if is_configured():
        return redirect(url_for("index"))

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

    if "mnemonic" not in wizard_state or not wizard_state.get("password_set"):
        flash("Please complete all setup steps", "error")
        return redirect(url_for("index"))

    try:
        # 1. Create spark-sidecar directory if needed
        MNEMONIC_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o750)

        # 2. Write mnemonic file with correct permissions
        mnemonic = wizard_state["mnemonic"]
        MNEMONIC_FILE.write_text(mnemonic + "\n")
        MNEMONIC_FILE.chmod(0o640)

        # Set group ownership to spark-sidecar
        try:
            spark_gid = grp.getgrnam("spark-sidecar").gr_gid
            os.chown(MNEMONIC_FILE, 0, spark_gid)
        except KeyError:
            # Group might not exist yet (shouldn't happen but be safe)
            pass

        # 3. Update LNbits env file with Spark configuration
        update_lnbits_env()

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
                print("[DEV MODE] Would start services: spark-sidecar, lnbits")
            else:
                subprocess.run(["systemctl", "start", "spark-sidecar.service"], check=False)
                subprocess.run(["systemctl", "start", "lnbits.service"], check=False)
                subprocess.run(["systemctl", "start", "lnbitspi-admin.service"], check=False)
                subprocess.run(["systemctl", "reload", "caddy.service"], check=False)

        threading.Thread(target=finalize, daemon=True).start()

        return render_template("complete.html")

    except Exception as e:
        flash(f"Setup failed: {str(e)}", "error")
        return render_template("error.html", error=str(e))


def update_lnbits_env():
    """Update /etc/lnbits/lnbits.env with Spark configuration"""
    api_token = secrets.token_hex(32)

    spark_config = f"""
# Spark L2 Sidecar Configuration (added by configurator)
LNBITS_BACKEND_WALLET_CLASS=LightsparkSparkWallet
SPARK_URL=http://127.0.0.1:8765
SPARK_TOKEN={api_token}
"""

    # Read existing env file
    if ENV_FILE.exists():
        existing = ENV_FILE.read_text()
    else:
        existing = ""

    # Check if Spark config already exists
    if "SPARK_URL" not in existing:
        # Append Spark configuration
        updated = existing.rstrip() + "\n" + spark_config
        ENV_FILE.write_text(updated)
        ENV_FILE.chmod(0o640)

    # Write matching API key for the Spark sidecar service
    SPARK_SIDECAR_ENV_FILE.write_text(f"SPARK_SIDECAR_API_KEY={api_token}\n")
    SPARK_SIDECAR_ENV_FILE.chmod(0o640)
    try:
        spark_gid = grp.getgrnam("spark-sidecar").gr_gid
        os.chown(SPARK_SIDECAR_ENV_FILE, 0, spark_gid)
    except KeyError:
        pass


@app.route("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "configured": is_configured()}


if __name__ == "__main__":
    # Run on loopback only (Caddy will proxy)
    app.run(host="127.0.0.1", port=8080, debug=False)
