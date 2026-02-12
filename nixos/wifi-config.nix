{ config, pkgs, lib, ... }:

{
  # Enable wpa_supplicant for Wi-Fi support
  # No predefined networks — wifi-config.service populates them dynamically
  networking.wireless.enable = true;

  # Oneshot service that reads wifi.txt from the firmware partition
  # and generates /etc/wpa_supplicant.conf before wpa_supplicant starts
  systemd.services.wifi-config = {
    description = "Configure Wi-Fi from wifi.txt on firmware partition";
    wantedBy = [ "multi-user.target" ];
    before = [ "wpa_supplicant.service" ];
    after = [ "local-fs.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
    path = with pkgs; [ coreutils gnused gawk wpa_supplicant ];
    script = ''
      WIFI_FILE="/boot/firmware/wifi.txt"
      WPA_CONF="/etc/wpa_supplicant.conf"

      # If wpa_supplicant.conf already has a network block, skip processing
      if [ -f "$WPA_CONF" ] && grep -q 'network={' "$WPA_CONF" 2>/dev/null; then
        echo "Wi-Fi already configured in $WPA_CONF, skipping."
        exit 0
      fi

      # Check if wifi.txt exists
      if [ ! -f "$WIFI_FILE" ]; then
        echo "No wifi.txt found on firmware partition, skipping Wi-Fi setup."
        exit 0
      fi

      # Read the file content, stripping UTF-8 BOM and Windows CRLF
      CONTENT=$(sed 's/\xEF\xBB\xBF//' "$WIFI_FILE" | sed 's/\r$//')

      # Check if this is a raw wpa_supplicant.conf (advanced users)
      if echo "$CONTENT" | grep -q '^network={'; then
        echo "Detected raw wpa_supplicant.conf format in wifi.txt"
        # Prepend ctrl_interface if not present
        if ! echo "$CONTENT" | grep -q 'ctrl_interface='; then
          printf 'ctrl_interface=/run/wpa_supplicant\nctrl_interface_group=wheel\nupdate_config=1\n\n' > "$WPA_CONF"
          echo "$CONTENT" >> "$WPA_CONF"
        else
          echo "$CONTENT" > "$WPA_CONF"
        fi
        chmod 0600 "$WPA_CONF"
        # Redact wifi.txt
        echo "# Wi-Fi configured. Original contents removed for security." > "$WIFI_FILE"
        echo "Wi-Fi configured from raw wpa_supplicant.conf format."
        exit 0
      fi

      # Check for SSID= line
      if ! echo "$CONTENT" | grep -q '^SSID='; then
        echo "wifi.txt exists but contains no SSID= line, skipping."
        exit 0
      fi

      # Parse key=value pairs (split only on first '=' to handle values with '=')
      SSID=""
      PASSWORD=""
      COUNTRY=""
      HIDDEN=""

      while IFS= read -r line; do
        # Skip comments and empty lines
        case "$line" in
          \#*|"") continue ;;
        esac

        key="''${line%%=*}"
        value="''${line#*=}"

        case "$key" in
          SSID)     SSID="$value" ;;
          PASSWORD) PASSWORD="$value" ;;
          COUNTRY)  COUNTRY="$value" ;;
          HIDDEN)   HIDDEN="$value" ;;
        esac
      done <<< "$CONTENT"

      if [ -z "$SSID" ]; then
        echo "Error: SSID is empty in wifi.txt"
        exit 1
      fi

      # Build wpa_supplicant.conf
      {
        echo "ctrl_interface=/run/wpa_supplicant"
        echo "ctrl_interface_group=wheel"
        echo "update_config=1"

        if [ -n "$COUNTRY" ]; then
          echo "country=$COUNTRY"
        fi

        echo ""

        if [ -z "$PASSWORD" ]; then
          # Open network (no password)
          echo "network={"
          echo "    ssid=\"$SSID\""
          echo "    key_mgmt=NONE"
          if [ "$HIDDEN" = "true" ]; then
            echo "    scan_ssid=1"
          fi
          echo "}"
        else
          # Use wpa_passphrase to hash the password (never store plaintext)
          WPA_BLOCK=$(wpa_passphrase "$SSID" "$PASSWORD" 2>/dev/null)
          if [ $? -ne 0 ]; then
            echo "Error: wpa_passphrase failed. Password must be 8-63 characters."
            exit 1
          fi

          # Remove the commented-out plaintext password line
          WPA_BLOCK=$(echo "$WPA_BLOCK" | grep -v '#psk=')

          # Add hidden network support if requested
          if [ "$HIDDEN" = "true" ]; then
            WPA_BLOCK=$(echo "$WPA_BLOCK" | sed '/^}$/i\    scan_ssid=1')
          fi

          echo "$WPA_BLOCK"
        fi
      } > "$WPA_CONF"

      chmod 0600 "$WPA_CONF"

      # Redact wifi.txt on the firmware partition (remove plaintext password from FAT32)
      echo "# Wi-Fi configured. Original contents removed for security." > "$WIFI_FILE"

      echo "Wi-Fi configured for SSID: $SSID"
    '';
  };

  # Place wifi.txt.example on the firmware partition at build time
  # so users can see it when browsing the SD card before first boot
  sdImage.populateFirmwareCommands = lib.mkAfter ''
    cat > firmware/wifi.txt.example << 'EXAMPLE'
# LNbitsBox Wi-Fi Configuration
#
# To connect to Wi-Fi, rename this file to wifi.txt
# and fill in your network details below.
#
# The password will be removed from this file after
# first boot for security.

SSID=YourNetworkName
PASSWORD=YourWiFiPassword

# Optional: Set your country code for regulatory compliance
# (two-letter ISO 3166-1 alpha-2 code, e.g., US, GB, DE)
# COUNTRY=US

# Optional: Set to true if your network is hidden
# HIDDEN=true
EXAMPLE
  '';
}
