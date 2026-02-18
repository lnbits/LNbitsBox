{ config, pkgs, spark-sidecar, ... }:

let
  sparkPkg = pkgs.callPackage ./spark-sidecar-package.nix { inherit spark-sidecar; };
  stateDir = "/var/lib/spark-sidecar";
  mnemonicFile = "${stateDir}/mnemonic";
in
{
  # Dedicated system user for the service
  users.users.spark-sidecar = {
    isSystemUser = true;
    group = "spark-sidecar";
  };
  users.groups.spark-sidecar = {};

  # State directory
  systemd.tmpfiles.rules = [
    "d ${stateDir} 0750 root spark-sidecar - -"
  ];

  systemd.services.spark-sidecar = {
    description = "Spark Lightning L2 sidecar";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    # Only start if the system has been configured
    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    serviceConfig = {
      Type = "simple";
      User = "spark-sidecar";
      Group = "spark-sidecar";

      # Environment variables for Spark sidecar
      Environment = [
        "SPARK_MNEMONIC_FILE=${mnemonicFile}"
        "SPARK_SIDECAR_PORT=8765"
        "SPARK_SIDECAR_HOST=127.0.0.1"
        "SPARK_NETWORK=MAINNET"
        "SPARK_PAY_WAIT_MS=20000"
      ];

      # API key written by the configurator during first-run setup
      EnvironmentFile = "${stateDir}/api-key.env";

      ExecStart = "${sparkPkg}/bin/spark-sidecar";

      Restart = "on-failure";
      RestartSec = 5;

      # Hardening options
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ stateDir ];
      LockPersonality = true;
    };
  };
}
