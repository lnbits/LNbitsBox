{ pkgs }:

pkgs.writeScriptBin "lnbitspi-reset" ''
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
  echo "  • Stop LNbits and Spark sidecar services"
  echo "  • Remove the configuration marker"
  echo "  • Re-enable the setup wizard"
  echo ""
  echo "This will NOT:"
  echo "  • Delete your LNbits data or database"
  echo "  • Delete your Spark mnemonic (unless you choose to)"
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
  systemctl stop spark-sidecar.service || true

  echo "Removing configuration marker..."
  rm -f /var/lib/lnbits/.configured

  echo "Reloading Caddy to route to configurator..."
  systemctl reload caddy.service || true

  echo ""
  echo "─────────────────────────────────────────────────────"
  echo "Mnemonic Management"
  echo "─────────────────────────────────────────────────────"
  if [ -f /var/lib/spark-sidecar/mnemonic ]; then
    echo "A Spark mnemonic file exists at:"
    echo "  /var/lib/spark-sidecar/mnemonic"
    echo ""
    echo "If you delete it, you will need to generate or import"
    echo "a new seed phrase. Make sure you have it backed up!"
    echo ""
    read -p "Delete the mnemonic file? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "Deleting mnemonic file..."
      rm -f /var/lib/spark-sidecar/mnemonic
      echo "Mnemonic deleted."
    else
      echo "Keeping mnemonic file (you can import it in the wizard)."
    fi
  else
    echo "No mnemonic file found. Skipping."
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
  echo "═══════════════════════════════════════════════════════"
  echo "  Reset Complete"
  echo "═══════════════════════════════════════════════════════"
  echo ""
  echo "The configuration wizard will be available at:"
  echo "  https://<this-device-ip>/"
  echo ""
  echo "The configurator service will start automatically."
  echo "LNbits and Spark sidecar will remain stopped until"
  echo "you complete the setup wizard."
  echo ""
''
