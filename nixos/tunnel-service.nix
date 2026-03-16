{ pkgs, ... }:

let
  stateDir = "/var/lib/lnbitsbox-tunnel";
  runtimeEnv = "${stateDir}/runtime.env";
  keyFile = "${stateDir}/reverse-proxy-key";
  startScript = pkgs.writeShellScript "lnbitsbox-reverse-tunnel" ''
    set -euo pipefail

    if [ ! -f "${runtimeEnv}" ]; then
      echo "Missing runtime env file: ${runtimeEnv}"
      exit 1
    fi

    # shellcheck disable=SC1091
    source "${runtimeEnv}"

    : "''${REMOTE_PORT:?REMOTE_PORT is required}"
    : "''${SSH_USER:?SSH_USER is required}"
    : "''${SSH_HOST:?SSH_HOST is required}"

    if [ ! -f "''${KEY_FILE:-${keyFile}}" ]; then
      echo "Missing key file: ''${KEY_FILE:-${keyFile}}"
      exit 1
    fi

    exec ${pkgs.autossh}/bin/autossh \
      -M 0 \
      -N \
      -o ServerAliveInterval=30 \
      -o ServerAliveCountMax=3 \
      -o ExitOnForwardFailure=yes \
      -o StrictHostKeyChecking=accept-new \
      -i "''${KEY_FILE:-${keyFile}}" \
      -R "''${REMOTE_PORT}:localhost:''${LOCAL_PORT:-5000}" \
      "''${SSH_USER}@''${SSH_HOST}"
  '';
in
{
  systemd.tmpfiles.rules = [
    "d ${stateDir} 0770 lnbitsadmin lnbitsadmin - -"
  ];

  systemd.services.lnbitsbox-reverse-tunnel = {
    description = "LNbitsBox Reverse SSH Tunnel";
    after = [ "network-online.target" "lnbits.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    path = [ pkgs.openssh pkgs.coreutils pkgs.bash ];

    serviceConfig = {
      Type = "simple";
      User = "root";
      Group = "root";

      ExecStart = startScript;
      Restart = "always";
      RestartSec = 5;

      # Keep filesystem mostly read-only while allowing tunnel state updates.
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ stateDir ];
      LockPersonality = true;
    };
  };
}
