{ config, pkgs, ... }:

{
  system.stateVersion = "24.11";

  # Specify the Raspberry Pi board (required by raspberry-pi-nix)
  raspberry-pi-nix.board = "bcm2711"; # Raspberry Pi 4

  networking.hostName = "lnbits-pi4";
  networking.useDHCP = true;

  # OpenSSH for headless access
  services.openssh.enable = true;
  services.openssh.settings = {
    PermitRootLogin = "no";
    PasswordAuthentication = true; # simple first boot; change to keys-only if you want
  };

  # Create a login user for first boot
  users.users.lnbitsadmin = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
    initialPassword = "lnbits";
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