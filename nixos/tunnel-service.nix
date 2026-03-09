{ pkgs, ... }:
{
  systemd.services.lnbitsbox-tunnel = {
    description = "LNbitsBox SSH Reverse Tunnel";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = "/var/lib/lnbitsbox-tunnel/command";

    serviceConfig = {
      Type = "simple";
      User = "root";
      Restart = "on-failure";
      RestartSec = "30s";
      ExecStart = "${pkgs.bash}/bin/bash -c 'exec $(cat /var/lib/lnbitsbox-tunnel/command)'";
    };
  };
}
