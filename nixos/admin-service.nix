{ config, pkgs, ... }:

let
  adminPkg = pkgs.callPackage ./admin-package.nix { };
in
{
  systemd.services.lnbitspi-admin = {
    description = "LNbitsBox admin dashboard";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    # Only run after system is configured
    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    # systemctl, wpa_cli, ip, ping must be in PATH
    path = [ pkgs.systemd pkgs.wpa_supplicant pkgs.iproute2 pkgs.iputils ];

    serviceConfig = {
      Type = "simple";
      # Runs as root for /etc/shadow access (PAM auth) and systemctl
      User = "root";
      Group = "root";

      ExecStart = "${adminPkg}/bin/lnbitspi-admin";

      Restart = "on-failure";
      RestartSec = 5;

      # PrivateTmp must be off: wpa_cli creates response sockets in /tmp
      # that wpa_supplicant (in a different unit) needs to reach.
      PrivateTmp = false;
    };
  };
}
