{ config, pkgs, lib, ... }:

let
  stateDir = "/var/lib/lnbitsbox-update";

  updateScript = pkgs.writeShellScript "lnbitsbox-update" ''
    set -euo pipefail

    STATE_DIR="${stateDir}"
    STATUS_FILE="$STATE_DIR/status"
    LOG_FILE="$STATE_DIR/log"
    TARGET_VERSION_FILE="$STATE_DIR/target-version"

    mkdir -p "$STATE_DIR"

    log() {
      echo "$(date -Iseconds) $*" | tee -a "$LOG_FILE"
    }

    set_status() {
      echo "$1" > "$STATUS_FILE"
      log "STATUS: $1"
    }

    cleanup_on_error() {
      set_status "failed"
      log "Update failed!"
      exit 1
    }
    trap cleanup_on_error ERR

    # Reset log for new update
    > "$LOG_FILE"

    RELEASE_TAG="''${1:-}"
    if [ -z "$RELEASE_TAG" ]; then
      log "ERROR: No release tag provided"
      set_status "failed"
      exit 1
    fi

    log "Starting update to release: $RELEASE_TAG"
    echo "$RELEASE_TAG" > "$TARGET_VERSION_FILE"

    # Step 1: Download manifest.json from GitHub Release
    set_status "downloading"
    log "Downloading manifest from GitHub Release..."

    MANIFEST_URL="https://github.com/lnbits/LNbitsBox/releases/download/$RELEASE_TAG/manifest.json"
    MANIFEST=$(${pkgs.curl}/bin/curl -fsSL "$MANIFEST_URL") || {
      log "ERROR: Failed to download manifest from $MANIFEST_URL"
      set_status "failed"
      exit 1
    }

    STORE_PATH=$(echo "$MANIFEST" | ${pkgs.jq}/bin/jq -r '.store_path')
    VERSION=$(echo "$MANIFEST" | ${pkgs.jq}/bin/jq -r '.version')

    if [ -z "$STORE_PATH" ] || [ "$STORE_PATH" = "null" ]; then
      log "ERROR: Invalid manifest — no store_path found"
      set_status "failed"
      exit 1
    fi

    log "Target store path: $STORE_PATH"
    log "Target version: $VERSION"

    # Step 2: Download the closure from Cachix
    log "Downloading system closure from binary cache..."
    ${pkgs.nix}/bin/nix copy --from https://lnbitsbox.cachix.org "$STORE_PATH" 2>&1 | tee -a "$LOG_FILE" || {
      log "ERROR: Failed to download closure from Cachix"
      set_status "failed"
      exit 1
    }
    log "Download complete."

    # Step 3: Set the new system profile
    set_status "activating"
    log "Setting new system profile..."
    ${pkgs.nix}/bin/nix-env -p /nix/var/nix/profiles/system --set "$STORE_PATH" 2>&1 | tee -a "$LOG_FILE" || {
      log "ERROR: Failed to set system profile"
      set_status "failed"
      exit 1
    }

    # Step 4: Activate the new configuration
    log "Activating new system configuration..."
    "$STORE_PATH/bin/switch-to-configuration" switch 2>&1 | tee -a "$LOG_FILE" || {
      log "ERROR: Failed to activate new configuration"
      set_status "failed"
      exit 1
    }

    set_status "success"
    log "Update complete! Now running version $VERSION"
  '';

in {
  # Ensure state directory exists
  systemd.tmpfiles.rules = [
    "d ${stateDir} 0755 root root -"
  ];

  # Initialize status file on activation
  system.activationScripts.lnbitsbox-update-init = ''
    mkdir -p ${stateDir}
    if [ ! -f ${stateDir}/status ]; then
      echo "idle" > ${stateDir}/status
    fi
  '';

  # Make the update script available system-wide
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "lnbitsbox-update" ''
      exec ${updateScript} "$@"
    '')
  ];

  # Allow the admin app service to run systemd-run for transient update units
  security.polkit.extraConfig = ''
    polkit.addRule(function(action, subject) {
      if (action.id === "org.freedesktop.systemd1.manage-units" &&
          subject.user === "root") {
        return polkit.Result.YES;
      }
    });
  '';
}
