{ config, pkgs, ... }:

let
  configuratorPkg = pkgs.callPackage ./configurator-package.nix { };
in
{
  systemd.services.lnbitspi-configurator = {
    description = "LNbitsPi first-run configuration wizard";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    # Only start if the system has NOT been configured
    unitConfig = {
      ConditionPathExists = "!/var/lib/lnbits/.configured";
    };

    # chpasswd (shadow) and systemctl (systemd) must be in PATH
    path = [ pkgs.shadow pkgs.systemd ];

    serviceConfig = {
      Type = "simple";
      # Run as root (needs permissions to set passwords, write files)
      User = "root";
      Group = "root";

      ExecStart = "${configuratorPkg}/bin/lnbitspi-configurator";

      Restart = "on-failure";
      RestartSec = 5;

      # Minimal hardening (less restrictive since it needs root access)
      PrivateTmp = true;
    };
  };
}
