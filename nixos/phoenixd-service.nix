{ config, pkgs, ... }:

let
  phoenixdPkg = pkgs.callPackage ./phoenixd-package.nix { };
  homeDir = "/var/lib/phoenixd";
  stateDir = "${homeDir}/.phoenix";
  seedFile = "${stateDir}/seed.dat";
  confFile = "${stateDir}/phoenix.conf";
  selectedFundingSourceFile = "/var/lib/lnbitsbox/funding-source";
in
{
  users.users.phoenixd = {
    isSystemUser = true;
    group = "phoenixd";
    home = homeDir;
    createHome = true;
  };
  users.groups.phoenixd = {};

  systemd.tmpfiles.rules = [
    "d ${homeDir} 0750 phoenixd phoenixd - -"
    "d ${stateDir} 0750 phoenixd phoenixd - -"
  ];

  system.activationScripts.phoenixd-config = ''
    mkdir -p ${homeDir}
    chown phoenixd:phoenixd ${homeDir}
    chmod 0750 ${homeDir}

    mkdir -p ${stateDir}
    chown phoenixd:phoenixd ${stateDir}
    chmod 0750 ${stateDir}

    if [ ! -f ${confFile} ]; then
      install -m 0640 -o phoenixd -g phoenixd /dev/null ${confFile}
      cat > ${confFile} << 'EOF'
chain=mainnet
http-bind-address=127.0.0.1
http-bind-port=9740
auto-liquidity=2000000
EOF
      printf 'http-password=%s\n' "$(${pkgs.openssl}/bin/openssl rand -hex 32)" >> ${confFile}
    fi
  '';

  systemd.services.phoenixd = {
    description = "Phoenixd Lightning funding source";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    path = [ pkgs.coreutils pkgs.gnugrep ];

    serviceConfig = {
      Type = "simple";
      User = "phoenixd";
      Group = "phoenixd";
      WorkingDirectory = homeDir;
      ExecCondition = "${pkgs.bash}/bin/bash -c 'test -f ${selectedFundingSourceFile} && grep -qx phoenixd ${selectedFundingSourceFile}'";
      ExecStart = "${pkgs.bash}/bin/bash -c 'printf \"I understand\\nI understand\\n\" | exec ${phoenixdPkg}/bin/phoenixd --seed-path ${seedFile}'";
      Restart = "on-failure";
      RestartSec = 5;
      LimitNOFILE = 4096;

      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ homeDir ];
      LockPersonality = true;
    };
  };

  environment.systemPackages = [ phoenixdPkg ];
}
