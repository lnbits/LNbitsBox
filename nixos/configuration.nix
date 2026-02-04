{ config, pkgs, ... }:

{
  system.stateVersion = "24.11";

  # Specify the Raspberry Pi board (required by raspberry-pi-nix)
  raspberry-pi-nix.board = "bcm2711"; # Raspberry Pi 4

  # Optional: Customize the firmware partition label (default is "FIRMWARE")
  raspberry-pi-nix.firmware-partition-label = "LNbitsPi";

  networking.hostName = "lnbits";
  networking.useDHCP = true;

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
    "consoleblank=0"
    "console=ttyAMA0,115200"  # Serial console (for UART debugging)
    "console=tty1"             # HDMI console (last = preferred/default)
  ];

  # Enable getty (login prompt) on tty1
  systemd.services."getty@tty1".enable = true;

  # Ensure autovt (automatic virtual terminals) are enabled
  systemd.services."autovt@tty1".enable = true;

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
  ];

  # LNbits listens on 9000
  networking.firewall.allowedTCPPorts = [ 9000 ];

  # Bring in LNbits service
  imports = [
    ./lnbits-service.nix
  ];

  # Pi4: 64-bit + UART enabled (optional but handy)
  hardware.raspberry-pi.config = {
    all.options = {
      arm_64bit.enable = true;
      arm_64bit.value = true;

      enable_uart.enable = true;
      enable_uart.value = true;
    };
    pi4 = { };
  };
}