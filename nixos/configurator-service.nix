{ config, pkgs, bark, fenix, ... }:

let
  configuratorPkg = pkgs.callPackage ./configurator-package.nix { };
  barkPkg = pkgs.callPackage ./barkd-package.nix { inherit bark fenix; };
in
{
  systemd.services.lnbitspi-configurator = {
    description = "LNbitsBox first-run setup wizard";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    # Only start if the system has NOT been configured
    unitConfig = {
      ConditionPathExists = "!/var/lib/lnbits/.configured";
    };

    # chpasswd (shadow) and systemctl (systemd) must be in PATH
    path = [ pkgs.shadow pkgs.systemd barkPkg ];

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
