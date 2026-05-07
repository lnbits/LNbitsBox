{ config, pkgs, arkade-sidecar, ... }:

let
  arkadePkg = pkgs.callPackage ./arkade-sidecar-package.nix { inherit arkade-sidecar; };
  stateDir = "/var/lib/arkade-sidecar";
  mnemonicFile = "${stateDir}/mnemonic";
  selectedFundingSourceFile = "/var/lib/lnbitsbox/funding-source";
in
{
  users.users.arkade-sidecar = {
    isSystemUser = true;
    group = "arkade-sidecar";
  };
  users.groups.arkade-sidecar = {};

  systemd.tmpfiles.rules = [
    "d ${stateDir} 0750 root arkade-sidecar - -"
  ];

  systemd.services.arkade-sidecar = {
    description = "Arkade Lightning sidecar";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    serviceConfig = {
      Type = "simple";
      User = "arkade-sidecar";
      Group = "arkade-sidecar";
      ExecCondition = "${pkgs.bash}/bin/bash -c 'test ! -f ${selectedFundingSourceFile} || grep -qx ark ${selectedFundingSourceFile}'";

      Environment = [
        "ARKADE_MNEMONIC_FILE=${mnemonicFile}"
        "ARKADE_ARK_SERVER_URL=https://arkade.computer"
        "ARKADE_BOLTZ_SERVER_URL=https://api.ark.boltz.exchange"
        "ARKADE_SIDECAR_HOST=127.0.0.1"
        "ARKADE_SIDECAR_PORT=8765"
        "ARKADE_NETWORK=mainnet"
        "ARKADE_IS_MAINNET=true"
        "ARKADE_SIDECAR_STATE_PATH=${stateDir}/arkade-sidecar-state.json"
        "ARKADE_STORAGE_PATH=${stateDir}/arkade-wallet.sqlite"
        "ARKADE_SWAP_STORAGE_PATH=${stateDir}/arkade-swaps.sqlite"
      ];

      EnvironmentFile = "${stateDir}/api-key.env";

      ExecStart = "${arkadePkg}/bin/arkade-sidecar";

      Restart = "on-failure";
      RestartSec = 5;

      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ stateDir ];
      LockPersonality = true;
    };
  };
}
