{ pkgs, arkade-sidecar }:

pkgs.buildNpmPackage {
  pname = "arkade-sidecar";
  version = "0.1.0";

  src = arkade-sidecar;
  npmDepsHash = "sha256-MUMCMmydH/UFJgKNuiYGVK2Z1EZGeK4azMnFm600iKI=";

  dontNpmBuild = true;
  dontBuild = true;

  npmFlags = [ "--legacy-peer-deps" ];

  postPatch = ''
    rm -f Makefile
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/arkade-sidecar
    cp -r . $out/lib/arkade-sidecar/

    mkdir -p $out/bin
    cat > $out/bin/arkade-sidecar << EOF
#!${pkgs.bash}/bin/bash
set -euo pipefail

MNEMONIC_FILE="\''${ARKADE_MNEMONIC_FILE:-/var/lib/arkade-sidecar/mnemonic}"

if [ ! -f "\$MNEMONIC_FILE" ]; then
  echo "Error: Arkade mnemonic file not found at \$MNEMONIC_FILE" >&2
  exit 1
fi

export ARKADE_MNEMONIC="\$(cat "\$MNEMONIC_FILE")"

cd $out/lib/arkade-sidecar
exec ${pkgs.nodejs}/bin/node server.mjs "\$@"
EOF

    chmod +x $out/bin/arkade-sidecar

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Arkade LNbits sidecar";
    homepage = "https://github.com/lnbits/arkade_sidecar";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
