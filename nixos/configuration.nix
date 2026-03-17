{ config, pkgs, version ? "dev", ... }:

{
  system.stateVersion = "24.11";

  # Write version to filesystem for the admin app to read
  environment.etc."lnbitsbox-version".text = version;

  # Enable flakes (needed for nix copy) and configure binary caches
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    substituters = [
      "https://cache.nixos.org"
      "https://lnbitsbox.cachix.org"
    ];
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "lnbitsbox.cachix.org-1:ODev9ZJ74MRM1rU5ITE7NhfpgJLyyQygjYP0Ug4aDyg="
    ];
  };

  # Auto garbage collect old generations
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 14d";
  };

  # Specify the Raspberry Pi board (required by raspberry-pi-nix)
  raspberry-pi-nix.board = "bcm2711"; # Raspberry Pi 4

  # Optional: Customize the firmware partition label (default is "FIRMWARE")
  raspberry-pi-nix.firmware-partition-label = "LNbitsBox";

  networking.hostName = "lnbits";
  networking.useDHCP = true;

  # Enable mDNS so the box is reachable via lnbits.local
  services.avahi = {
    enable = true;
    nssmdns4 = true;
    publish = {
      enable = true;
      addresses = true;
    };
  };

  # OpenSSH for headless access
  services.openssh.enable = true;
  services.openssh.settings = {
    PermitRootLogin = "no";
    PasswordAuthentication = true; # disabled in practice until configurator sets a real user password
  };

  # Enable console on HDMI (keeps display active and shows login prompt)
  # When multiple consoles are specified, the LAST one becomes the default/preferred
  # We list serial first, then tty1 last so HDMI is the preferred console
  boot.kernelParams = [
    "consoleblank=0"           # Disable console blanking
    "console=ttyAMA0,115200"   # Serial console (for UART debugging)
    "console=tty1"             # HDMI console (last = preferred/default)
    "fbcon=map:0"              # Force framebuffer console on fb0
    "vt.global_cursor_default=0" # Keep cursor visible
    "logo.nologo"              # Skip boot logo (cleaner console output)
    "loglevel=4"               # Show boot messages (4=warning, 7=debug)
  ];

  # Disable screen blanking at the systemd level
  powerManagement.enable = false;
  services.logind.extraConfig = ''
    HandlePowerKey=ignore
    HandleSuspendKey=ignore
    HandleHibernateKey=ignore
    HandleLidSwitch=ignore
  '';

  # Create a login user for first boot
  # Change the username by modifying "lnbitsadmin" below
  users.users.lnbitsadmin = {
    isNormalUser = true;
    extraGroups = [ "wheel" ]; # wheel = sudo access

    # Ship without a usable password. The configurator assigns the first
    # real SSH password, and an optional authorized_keys file on the
    # firmware partition can enable headless key-based access before setup.
    hashedPassword = "$y$j9T$rJ6NmGZ7zE0U4N2hW0g2P.$e6TQ5QliNd3I.M0A2Y2vG7tUc1IQQ6pwT0nMY5myoN5";
  };

  security.sudo.wheelNeedsPassword = true;

  environment.systemPackages = with pkgs; [
    curl
    htop
    vim
    (pkgs.callPackage ./reset-configurator.nix { })
  ];

  systemd.services.lnbitsbox-firstboot-authorized-keys = {
    description = "Import optional first-boot SSH authorized_keys";
    wantedBy = [ "multi-user.target" ];
    before = [ "sshd.service" ];
    after = [ "local-fs.target" "users.target" ];
    unitConfig = {
      ConditionPathExists = "!/var/lib/lnbits/.configured";
    };
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
    path = with pkgs; [ coreutils gnused shadow ];
    script = ''
      KEY_SOURCE="/boot/firmware/authorized_keys"
      TARGET_HOME="/home/lnbitsadmin"
      TARGET_DIR="$TARGET_HOME/.ssh"
      TARGET_FILE="$TARGET_DIR/authorized_keys"

      if [ ! -s "$KEY_SOURCE" ]; then
        echo "No first-boot authorized_keys file found."
        exit 0
      fi

      if [ -e "$TARGET_FILE" ]; then
        echo "authorized_keys already exists for lnbitsadmin, skipping import."
        exit 0
      fi

      USER_GROUP="$(id -gn lnbitsadmin)"

      install -d -m 0700 -o lnbitsadmin -g "$USER_GROUP" "$TARGET_DIR"
      sed '/^[[:space:]]*$/d; s/\r$//' "$KEY_SOURCE" > "$TARGET_FILE"
      chown lnbitsadmin:"$USER_GROUP" "$TARGET_FILE"
      chmod 0600 "$TARGET_FILE"

      echo "Imported SSH authorized_keys for lnbitsadmin from firmware partition."
    '';
  };

  # Display first-boot instructions on login
  environment.etc."motd".text = ''
    ╔═══════════════════════════════════════════════════════════╗
    ║                    Welcome to LNbitsBox                   ║
    ╚═══════════════════════════════════════════════════════════╝

    To configure your device, open a web browser and navigate to:
      https://<this-device-ip>/

    Not configured yet? The setup wizard will guide you through:
      • Generating/importing your Spark wallet seed phrase
      • Setting your SSH password
      • Launching LNbits

    Optional headless SSH before setup:
      • Put your public keys in /boot/firmware/authorized_keys
      • Sign in as lnbitsadmin using key-based auth
      • There is no default SSH password on the image

    Already configured? LNbits is available at the same URL.

    To find this device's IP address, run: ip addr show
    To reset configuration, run: sudo lnbitspi-reset
  '';

  # Caddy reverse proxy (ports 80 + 443)
  # Caddy routes to configurator (pre-setup) or LNbits (post-setup)
  networking.firewall.allowedTCPPorts = [ 80 443 ];

  # Import service modules
  imports = [
    ./lnbits-service.nix
    ./spark-sidecar-service.nix
    ./configurator-service.nix
    ./caddy-proxy.nix
    ./admin-service.nix
    ./tor-service.nix
    ./tunnel-service.nix
    ./usb-storage.nix
    ./wifi-config.nix
    ./welcome-screen.nix
    ./update-service.nix
  ];

  # Auto-migration for existing LNbits installations
  # If database exists but no marker file, create marker to skip wizard
  system.activationScripts.lnbits-migration = ''
    if [ -f /var/lib/lnbits/database.sqlite3 ] && [ ! -f /var/lib/lnbits/.configured ]; then
      echo "Existing LNbits installation detected, auto-migrating..."
      touch /var/lib/lnbits/.configured
      echo "Migration complete. Wizard will be skipped."
    fi
  '';

  # Pi4: 64-bit + UART enabled (optional but handy)
  hardware.raspberry-pi.config = {
    all.options = {
      arm_64bit.enable = true;
      arm_64bit.value = true;

      enable_uart.enable = true;
      enable_uart.value = true;

      # Force HDMI output (prevents display from turning off)
      hdmi_force_hotplug.enable = true;
      hdmi_force_hotplug.value = true;

      # Auto-detect connected displays
      display_auto_detect.enable = true;
      display_auto_detect.value = true;

      # Disable overscan (removes black borders)
      disable_overscan.enable = true;
      disable_overscan.value = true;

      # Keep HDMI output active even when no signal detected
      hdmi_blanking.enable = true;
      hdmi_blanking.value = false;
    };
    pi4 = { };
  };

  # Enable VC4 graphics driver for HDMI output
  # This prevents the console from switching to dummy device
  hardware.graphics.enable = true;

  # Ensure framebuffer console stays active
  boot.kernelModules = [ "vc4" "bcm2835_dma" "i2c_bcm2835" ];
}
