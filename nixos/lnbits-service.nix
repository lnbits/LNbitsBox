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

  # Directories
  systemd.tmpfiles.rules = [
    "d ${dataDir} 0750 lnbits lnbits - -"
    "d /etc/lnbits 0755 root root - -"
  ];

  # Create default env file with proper multi-line content
  # This ensures all required variables are present
  system.activationScripts.lnbits-env = ''
    if [ ! -f ${envFile} ]; then
      cat > ${envFile} << 'EOF'
LNBITS_ADMIN_UI=true
LNBITS_HOST=0.0.0.0
LNBITS_PORT=9000
EOF
      chmod 0640 ${envFile}
      chown root:root ${envFile}
    fi
  '';

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
          --host ''${LNBITS_HOST} \
          --port ''${LNBITS_PORT}
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