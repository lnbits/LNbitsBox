{ config, pkgs, lnbits, ... }:

let
  lnbitsPkg = lnbits.packages.${pkgs.system}.default;
  dataDir = "/var/lib/lnbits";
  envFile = "/etc/lnbits/lnbits.env";
in
{
  # Dedicated system user for the service
  users.users.lnbits = {
    isSystemUser = true;
    group = "lnbits";
  };
  users.groups.lnbits = {};

  # Directories + default env file
  systemd.tmpfiles.rules = [
    "d ${dataDir} 0750 lnbits lnbits - -"
    "d /etc/lnbits 0755 root root - -"

    # Created if missing. Users can edit later.
    # Add SUPER_USER=... here once you’ve created a user in LNbits.
    "f ${envFile} 0640 root root - LNBITS_ADMIN_UI=true\nLNBITS_HOST=0.0.0.0\nLNBITS_PORT=9000\n"
  ];

  systemd.services.lnbits = {
    description = "LNbits server";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      User = "lnbits";
      Group = "lnbits";

      EnvironmentFile = envFile;

      # Persist LNbits data
      Environment = [
        "LNBITS_DATA_FOLDER=${dataDir}"
      ];

      ExecStart = ''
        ${lnbitsPkg}/bin/lnbits \
          --host ''${LNBITS_HOST:-0.0.0.0} \
          --port ''${LNBITS_PORT:-9000}
      '';

      Restart = "on-failure";
      RestartSec = 2;

      # Basic hardening options
      # Note: MemoryDenyWriteExecute is NOT enabled because pynostr (used by LNbits
      # for Nostr Wallet Connect) requires write+execute memory for ffi.callback()
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ dataDir "/etc/lnbits" ];
      LockPersonality = true;
    };
  };
}