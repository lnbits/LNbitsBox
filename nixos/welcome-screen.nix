{ config, pkgs, lib, ... }:

let
  welcomeScript = pkgs.writeShellScript "lnbitsbox-welcome" ''
    export PATH="${lib.makeBinPath [ pkgs.coreutils pkgs.iproute2 pkgs.iputils pkgs.systemd pkgs.ncurses ]}:$PATH"

    # Hide cursor, restore on exit
    tput civis 2>/dev/null
    trap 'tput cnorm 2>/dev/null' EXIT INT TERM

    # Colors
    PINK='\033[38;5;198m'
    GREEN='\033[32m'
    YELLOW='\033[33m'
    RED='\033[31m'
    GRAY='\033[90m'
    BOLD='\033[1m'
    DIM='\033[2m'
    RESET='\033[0m'

    service_status() {
      local svc="$1"
      local state
      state=$(systemctl is-active "$svc" 2>/dev/null)
      case "$state" in
        active)     printf "''${GREEN}●''${RESET} running" ;;
        activating) printf "''${YELLOW}◐''${RESET} starting" ;;
        failed)     printf "''${RED}✗''${RESET} failed" ;;
        *)          printf "''${GRAY}○''${RESET} stopped" ;;
      esac
    }

    while true; do
      # --- Gather data ---
      configured=false
      [ -f /var/lib/lnbits/.configured ] && configured=true

      # Network
      ips=$(ip -4 addr show scope global 2>/dev/null \
        | ${pkgs.gawk}/bin/awk '/inet / { split($2,a,"/"); print a[1] }')
      ip_list=""
      ip_count=0
      while IFS= read -r addr; do
        [ -z "$addr" ] && continue
        ip_count=$((ip_count + 1))
        if [ -n "$ip_list" ]; then
          ip_list="$ip_list, $addr"
        else
          ip_list="$addr"
        fi
      done <<< "$ips"

      if [ "$ip_count" -eq 0 ]; then
        ip_display="No network connection"
      else
        ip_display="$ip_list"
      fi

      # Internet connectivity
      if ping -c1 -W2 1.1.1.1 >/dev/null 2>&1; then
        inet="''${GREEN}●''${RESET} Connected"
      else
        inet="''${RED}✗''${RESET} No internet"
      fi

      # Tor onion address
      onion=""
      if [ -f /var/lib/tor/onion/lnbits/hostname ]; then
        onion=$(cat /var/lib/tor/onion/lnbits/hostname 2>/dev/null)
      fi

      # Service statuses
      spark_status=$(service_status spark-sidecar)
      lnbits_status=$(service_status lnbits)
      caddy_status=$(service_status caddy)
      tor_status=$(service_status tor)

      # System info
      now=$(date '+%Y-%m-%d %H:%M:%S')

      cpu_temp=""
      if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        raw=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
        if [ -n "$raw" ]; then
          cpu_temp="$((raw / 1000))°C"
        fi
      fi

      # --- Render ---
      clear

      # ASCII logo in pink
      printf "''${PINK}"
      cat << 'LOGO'

  ██╗     ███╗   ██╗██████╗ ██╗████████╗███████╗██████╗  ██████╗ ██╗  ██╗
  ██║     ████╗  ██║██╔══██╗██║╚══██╔══╝██╔════╝██╔══██╗██╔═══██╗╚██╗██╔╝
  ██║     ██╔██╗ ██║██████╔╝██║   ██║   ███████╗██████╔╝██║   ██║ ╚███╔╝
  ██║     ██║╚██╗██║██╔══██╗██║   ██║   ╚════██║██╔══██╗██║   ██║ ██╔██╗
  ███████╗██║ ╚████║██████╔╝██║   ██║   ███████║██████╔╝╚██████╔╝██╔╝ ██╗
  ╚══════╝╚═╝  ╚═══╝╚═════╝ ╚═╝   ╚═╝   ╚══════╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
LOGO
      printf "''${RESET}\n"

      if [ "$configured" = true ]; then
        # --- Configured mode ---
        printf "  ''${BOLD}Services''${RESET}\n"
        printf "    Spark Sidecar   %b\n" "$spark_status"
        printf "    LNbits          %b\n" "$lnbits_status"
        printf "    Caddy           %b\n" "$caddy_status"
        printf "    Tor             %b\n" "$tor_status"
        printf "\n"

        printf "  ''${BOLD}Network''${RESET}\n"
        printf "    IP Address      %s\n" "$ip_display"
        printf "    Internet        %b\n" "$inet"
        if [ -n "$onion" ]; then
          printf "    Tor Onion       %s\n" "$onion"
        fi
        printf "\n"

        printf "  ''${BOLD}Access LNbits''${RESET}\n"
        if [ "$ip_count" -gt 0 ]; then
          first_ip=$(echo "$ips" | head -1)
          printf "    https://%s/\n" "$first_ip"
        else
          printf "    ''${DIM}Waiting for network...''${RESET}\n"
        fi
      else
        # --- Unconfigured mode ---
        printf "  ''${YELLOW}''${BOLD}  ⚡ SETUP REQUIRED ⚡''${RESET}\n\n"

        if [ "$ip_count" -gt 0 ]; then
          first_ip=$(echo "$ips" | head -1)
          printf "  Open a browser and go to:\n"
          printf "    ''${BOLD}http://lnbits.local/''${RESET} or ''${BOLD}https://%s/''${RESET}\n\n" "$first_ip"
          printf "  The setup wizard will guide you through:\n"
          printf "    • Generating your Spark wallet seed phrase\n"
          printf "    • Setting a SSH password\n"
          printf "    • Launching LNbits\n"
        else
          printf "  ''${RED}No network connection detected.''${RESET}\n\n"
          printf "  Connect an Ethernet cable or configure Wi-Fi:\n"
          printf "    1. Remove the SD card\n"
          printf "    2. Edit wifi.txt on the LNbitsBox partition\n"
          printf "    3. Re-insert and reboot\n"
        fi
      fi

      printf "\n"
      printf "  ''${BOLD}System''${RESET}\n"
      if [ -n "$cpu_temp" ]; then
        printf "    CPU Temp        %s\n" "$cpu_temp"
      fi
      printf "    Time            %s\n" "$now"

      printf "\n"
      printf "  ''${DIM}Press Alt+F2 for login shell''${RESET}\n"

      sleep 30
    done
  '';

in
{
  # Disable getty on tty1 — we'll use it for our dashboard
  systemd.services."getty@tty1".wantedBy = lib.mkForce [];

  # Enable getty on tty2 so users can still get a login shell via Alt+F2
  systemd.services."getty@tty2" = {
    enable = true;
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Restart = "always";
      RestartSec = "0";
    };
  };

  # Welcome dashboard on tty1
  systemd.services.lnbitsbox-welcome = {
    description = "LNbitsBox Welcome Dashboard";
    after = [ "systemd-user-sessions.service" "network-online.target" ];
    wants = [ "network-online.target" ];
    conflicts = [ "getty@tty1.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = welcomeScript;
      StandardInput = "tty";
      StandardOutput = "tty";
      TTYPath = "/dev/tty1";
      TTYReset = "yes";
      TTYVHangup = "yes";
      TTYVTDisallocate = "yes";
      Restart = "always";
      RestartSec = "3";
      UtmpIdentifier = "tty1";
    };
  };
}
