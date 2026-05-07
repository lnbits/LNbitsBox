{ pkgs }:

let
  resetScript = pkgs.writeShellScriptBin "lnbitspi-reset" ''
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
      echo "Error: This command must be run as root (use sudo)"
      exit 1
    fi

    echo "═══════════════════════════════════════════════════════"
    echo "  LNbitsBox Configuration Reset"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "This will:"
    echo "  • Stop LNbits, admin, and funding source services"
    echo "  • Remove the configuration marker"
    echo "  • Re-enable the setup wizard"
    echo ""
    echo "This will NOT:"
    echo "  • Delete your LNbits data or database"
    echo "  • Delete your funding-source seed phrase (unless you choose to)"
    echo ""
    read -p "Continue with reset? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Reset cancelled."
      exit 0
    fi

    echo ""
    echo "Stopping services..."
    systemctl stop lnbits.service || true
    systemctl stop lnbitspi-admin.service || true
    systemctl stop spark-sidecar.service || true
    systemctl stop phoenixd.service || true
    systemctl stop arkade-sidecar.service || true

    echo "Removing configuration marker..."
    if [ -e /var/lib/lnbits/.configured ]; then
      rm -f /var/lib/lnbits/.configured
    fi

    if [ -e /var/lib/lnbits/.configured ]; then
      echo "Error: failed to remove /var/lib/lnbits/.configured"
      exit 1
    fi

    echo "Starting configurator service..."
    systemctl reset-failed lnbitspi-configurator.service || true
    systemctl start lnbitspi-configurator.service || true

    echo "Reloading Caddy to route to configurator..."
    systemctl reload caddy.service || true

    echo ""
    echo "─────────────────────────────────────────────────────"
    echo "Seed Phrase Management"
    echo "─────────────────────────────────────────────────────"
    if [ -f /var/lib/spark-sidecar/mnemonic ] || [ -f /var/lib/arkade-sidecar/mnemonic ] || [ -f /var/lib/phoenixd/.phoenix/seed.dat ]; then
      if [ -f /var/lib/spark-sidecar/mnemonic ]; then
        seed_file="/var/lib/spark-sidecar/mnemonic"
        seed_name="Spark"
      elif [ -f /var/lib/arkade-sidecar/mnemonic ]; then
        seed_file="/var/lib/arkade-sidecar/mnemonic"
        seed_name="Ark"
      else
        seed_file="/var/lib/phoenixd/.phoenix/seed.dat"
        seed_name="Phoenixd"
      fi
      echo "A $seed_name seed file exists at:"
      echo "  $seed_file"
      echo ""
      echo "If you delete it, you will need to generate or import"
      echo "a new seed phrase. Make sure you have it backed up!"
      echo ""
      read -p "Delete the seed file? [y/N] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting seed file..."
        rm -f "$seed_file"
        echo "Seed file deleted."
      else
        echo "Keeping seed file (you can import it in the wizard)."
      fi
    else
      echo "No funding-source seed file found. Skipping."
    fi

    echo ""
    echo "─────────────────────────────────────────────────────"
    echo "Root CA Certificate Management"
    echo "─────────────────────────────────────────────────────"
    if [ -f /var/lib/caddy/ca-cert.pem ]; then
      echo "A Root CA certificate exists at:"
      echo "  /var/lib/caddy/ca-cert.pem"
      echo ""
      echo "If you regenerate it, all devices that trusted the"
      echo "old CA will need to download and install the new one."
      echo ""
      read -p "Regenerate the Root CA certificate? [y/N] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting CA and server certificates..."
        rm -f /var/lib/caddy/ca-cert.pem
        rm -f /var/lib/caddy/ca-key.pem
        rm -f /var/lib/caddy/cert.pem
        rm -f /var/lib/caddy/key.pem
        echo "Certificates deleted. New ones will be generated on next boot."
      else
        echo "Keeping existing Root CA certificate."
      fi
    else
      echo "No Root CA certificate found. One will be generated on next boot."
    fi

    echo ""
    echo "─────────────────────────────────────────────────────"
    echo "Wi-Fi Configuration"
    echo "─────────────────────────────────────────────────────"
    if [ -f /etc/wpa_supplicant.conf ] && grep -q 'network={' /etc/wpa_supplicant.conf 2>/dev/null; then
      echo "A Wi-Fi configuration exists at:"
      echo "  /etc/wpa_supplicant.conf"
      echo ""
      echo "If you reset it, you can drop a new wifi.txt on the"
      echo "SD card firmware partition and reboot to reconfigure."
      echo ""
      read -p "Reset Wi-Fi configuration? [y/N] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing Wi-Fi configuration..."
        rm -f /etc/wpa_supplicant.conf
        systemctl restart wpa_supplicant.service || true
        echo "Wi-Fi configuration removed."
      else
        echo "Keeping Wi-Fi configuration."
      fi
    else
      echo "No Wi-Fi configuration found. Skipping."
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  Reset Complete"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "The configuration wizard will be available at:"
    echo "  https://<this-device-ip>/"
    echo ""
    echo "The configurator service has been started."
    echo "LNbits, admin, and funding source services will remain stopped until"
    echo "you complete the setup wizard."
    echo ""
  '';

  factoryResetScript = pkgs.writeShellScriptBin "lnbitspi-factory-reset" ''
    #!/usr/bin/env bash
    set -euo pipefail

    RM=${pkgs.coreutils}/bin/rm
    SYSTEMCTL=${pkgs.systemd}/bin/systemctl

    if [ "$EUID" -ne 0 ]; then
      echo "Error: This command must be run as root"
      exit 1
    fi

    remove_path() {
      local target="$1"
      if [ -e "$target" ] || [ -L "$target" ]; then
        "$RM" -rf "$target"
      fi
    }

    echo "Stopping LNbitsBox services for factory reset..."
    "$SYSTEMCTL" stop lnbits.service || true
    "$SYSTEMCTL" stop lnbitspi-admin.service || true
    "$SYSTEMCTL" stop spark-sidecar.service || true
    "$SYSTEMCTL" stop phoenixd.service || true
    "$SYSTEMCTL" stop arkade-sidecar.service || true
    "$SYSTEMCTL" stop lnbitsbox-reverse-tunnel.service || true

    echo "Removing LNbits and wallet state..."
    remove_path /var/lib/lnbits
    remove_path /var/lib/lnbits-extensions
    remove_path /var/lib/spark-sidecar
    remove_path /var/lib/arkade-sidecar
    remove_path /var/lib/phoenixd/.phoenix
    remove_path /var/lib/lnbitsbox
    remove_path /var/lib/lnbitsbox-tunnel
    remove_path /var/lib/lnbitsbox-recovery
    remove_path /etc/lnbits/lnbits.env

    echo "Re-enabling the configurator..."
    "$SYSTEMCTL" reset-failed lnbitspi-configurator.service || true
    "$SYSTEMCTL" start lnbitspi-configurator.service || true
    "$SYSTEMCTL" reload caddy.service || true

    echo "Factory reset complete."
  '';
in
pkgs.symlinkJoin {
  name = "lnbitsbox-reset-tools";
  paths = [
    resetScript
    factoryResetScript
  ];
}
