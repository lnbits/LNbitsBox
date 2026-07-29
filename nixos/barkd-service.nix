{ config, pkgs, bark, fenix, ... }:

let
  barkPkg = pkgs.callPackage ./barkd-package.nix { inherit bark fenix; };
  stateDir = "/var/lib/barkd";
  initDir = "/run/lnbitsbox-bark-init";
  initMnemonicFile = "${initDir}/mnemonic";
  selectedFundingSourceFile = "/var/lib/lnbitsbox/funding-source";
in
{
  users.users.barkd = {
    isSystemUser = true;
    group = "barkd";
  };
  users.groups.barkd = {};

  systemd.tmpfiles.rules = [
    "d ${stateDir} 0750 barkd barkd - -"
    "d ${initDir} 0750 root barkd - -"
  ];

  systemd.services.barkd = {
    description = "Bark wallet daemon for LNbits";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    path = [ pkgs.gnugrep ];

    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    serviceConfig = {
      Type = "simple";
      User = "barkd";
      Group = "barkd";
      StateDirectory = "barkd";
      StateDirectoryMode = "0750";
      ExecCondition = "${pkgs.bash}/bin/bash -c 'test ! -f ${selectedFundingSourceFile} || ${pkgs.gnugrep}/bin/grep -qx bark ${selectedFundingSourceFile}'";
      Environment = [
        "BARKD_DATADIR=${stateDir}"
        "BARKD_BIND_HOST=127.0.0.1"
        "BARKD_BIND_PORT=3000"
        "BARKD_EXPOSE_MNEMONIC=false"
      ];
      ExecStart = "${barkPkg}/bin/barkd";
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

  # The configurator starts this unit before creating the configured marker.
  # It starts a temporary local daemon, creates the wallet through its
  # authenticated REST API, then exits so barkd.service can own it normally.
  systemd.services.lnbitsbox-bark-init = {
    description = "Initialize Bark wallet for LNbitsBox setup";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    path = [ barkPkg pkgs.coreutils pkgs.curl pkgs.gnugrep pkgs.jq ];

    serviceConfig = {
      Type = "oneshot";
      User = "barkd";
      Group = "barkd";
      UMask = "0077";
      TimeoutStartSec = "90s";
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ stateDir initDir ];
      LockPersonality = true;
    };

    script = ''
      set -euo pipefail

      test -s ${initMnemonicFile}
      test ! -e ${stateDir}/db.sqlite

      BARKD_DATADIR=${stateDir} \
        BARKD_BIND_HOST=127.0.0.1 \
        BARKD_BIND_PORT=3000 \
        BARKD_EXPOSE_MNEMONIC=false \
        barkd &
      barkd_pid=$!
      cleanup() {
        kill "$barkd_pid" 2>/dev/null || true
        wait "$barkd_pid" 2>/dev/null || true
      }
      trap cleanup EXIT

      for _ in $(seq 1 30); do
        if test -s ${stateDir}/auth_token && curl --fail --silent --output /dev/null \
          -H "Authorization: Bearer $(cat ${stateDir}/auth_token)" \
          http://127.0.0.1:3000/api/v1/wallet/connected; then
          break
        fi
        sleep 1
      done

      test -s ${stateDir}/auth_token
      wallet_request=$(jq -n \
        --rawfile mnemonic ${initMnemonicFile} \
        '{ark_server: "ark.second.tech", chain_source: {esplora: {url: "https://mempool.second.tech/api"}}, network: "mainnet", mnemonic: $mnemonic}')
      curl --fail --silent --show-error \
        -H "Authorization: Bearer $(cat ${stateDir}/auth_token)" \
        -H "Content-Type: application/json" \
        --data "$wallet_request" \
        http://127.0.0.1:3000/api/v1/wallet >/dev/null
      test -s ${stateDir}/db.sqlite
      rm -f ${initMnemonicFile}
    '';
  };
}
