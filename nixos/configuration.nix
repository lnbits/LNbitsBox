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
    PasswordAuthentication = true; # simple first boot; change to keys-only if you want
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

    # Option 1: Set initial password (plaintext - stored in /nix/store)
    # User can change it after first login with 'passwd'
    initialPassword = "lnbits";

    # Option 2: Use a hashed password (more secure - see example below)
    # hashedPassword = "$y$j9T$...your-hashed-password-here...";
    # Generate with: mkpasswd -m yescrypt
  };

  security.sudo.wheelNeedsPassword = true;

  environment.systemPackages = with pkgs; [
    curl
    htop
    vim
    (pkgs.callPackage ./reset-configurator.nix { })
  ];

  # Display first-boot instructions on login
  environment.etc."motd".text = ''
    ╔═══════════════════════════════════════════════════════════╗
    ║                    Welcome to LNbitsBox                    ║
    ╚═══════════════════════════════════════════════════════════╝

    To configure your device, open a web browser and navigate to:
      https://<this-device-ip>/

    Not configured yet? The setup wizard will guide you through:
      • Generating/importing your Spark wallet seed phrase
      • Setting your SSH password
      • Launching LNbits

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
    ./wifi-config.nix
    ./welcome-screen.nix
    ./update-service.nix
  ];

  # Auto-migration for existing LNbits installations
  # If database exists but no marker file, create marker to skip wizard
  system.activationScripts.lnbits-migration = ''
    if [ -f /var/lib/lnbits/database.sqlite ] && [ ! -f /var/lib/lnbits/.configured ]; then
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