{ pkgs, ... }:

let
  stateDir = "/var/lib/lnbitsbox-tunnel";
  stateFile = "${stateDir}/state.json";
  runtimeEnv = "${stateDir}/runtime.env";
  keyFile = "${stateDir}/reverse-proxy-key";
  startScript = pkgs.writeShellScript "lnbitsbox-reverse-tunnel" ''
    set -euo pipefail

    if [ ! -f "${runtimeEnv}" ] && [ -f "${stateFile}" ]; then
      ${pkgs.python3}/bin/python3 - <<'PY'
import json
import shlex
from pathlib import Path

state_file = Path("${stateFile}")
runtime_env = Path("${runtimeEnv}")
key_file = Path("${keyFile}")

try:
    state = json.loads(state_file.read_text(encoding="utf-8"))
except Exception:
    state = {}

tunnel = state.get("current_tunnel") or {}
tunnel_id = tunnel.get("tunnel_id")
remote_port = tunnel.get("remote_port")

if tunnel_id and remote_port:
    ssh_user = str(tunnel.get("ssh_user") or "ubuntu")
    ssh_host = str(tunnel.get("ssh_host") or "lnpro.xyz")
    runtime_env.write_text(
        "\n".join(
            [
                f"REMOTE_PORT={int(remote_port)}",
                f"SSH_USER={shlex.quote(ssh_user)}",
                f"SSH_HOST={shlex.quote(ssh_host)}",
                f"KEY_FILE={shlex.quote(str(key_file))}",
                "LOCAL_PORT=5000",
                "AUTOSSH_GATETIME=0",
                "AUTOSSH_POLL=30",
                "AUTOSSH_FIRST_POLL=30",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    runtime_env.chmod(0o600)
PY
    fi

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
    "d ${stateDir} 0700 root root - -"
  ];

  systemd.services.lnbitsbox-reverse-tunnel = {
    description = "LNbitsBox Reverse SSH Tunnel";
    after = [ "network-online.target" "lnbits.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    unitConfig = {
      ConditionPathExists = "/var/lib/lnbits/.configured";
    };

    path = [ pkgs.openssh pkgs.coreutils pkgs.bash pkgs.python3 ];

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
