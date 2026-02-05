{ pkgs, spark-sidecar }:

pkgs.buildNpmPackage {
  pname = "spark-sidecar";
  version = "0.1.0";

  src = spark-sidecar;

  # To get the correct hash:
  # 1. Set to empty string initially: npmDepsHash = "";
  # 2. Run: nix build .#nixosConfigurations.pi4.config.system.build.toplevel
  # 3. Copy the hash from the error message
  # 4. Update this field with the correct hash
  npmDepsHash = "sha256-IF87onWOqsv3vtrGWpP95zaaUpRtKiDJ5NokNWDAzEQ=";

  # Skip npm scripts that might fail in sandbox
  npmBuildScript = "build";
  npmFlags = [ "--legacy-peer-deps" ];

  # Install phase: copy built files to output
  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/spark-sidecar
    cp -r * $out/lib/spark-sidecar/

    # Create wrapper script that loads mnemonic from file
    mkdir -p $out/bin
    cat > $out/bin/spark-sidecar << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

MNEMONIC_FILE="''${SPARK_MNEMONIC_FILE:-/var/lib/spark-sidecar/mnemonic}"

if [ ! -f "$MNEMONIC_FILE" ]; then
  echo "Error: Mnemonic file not found at $MNEMONIC_FILE" >&2
  exit 1
fi

# Read mnemonic from file and export as environment variable
export SPARK_MNEMONIC=$(cat "$MNEMONIC_FILE")

# Execute spark_sidecar with all arguments
cd $out/lib/spark-sidecar
exec ${pkgs.nodejs}/bin/node dist/index.js "$@"
EOF

    chmod +x $out/bin/spark-sidecar

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Spark Lightning L2 sidecar for LNbits";
    homepage = "https://github.com/lnbits/spark_sidecar";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
