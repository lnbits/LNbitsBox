{ pkgs }:

let
  python = pkgs.python3.withPackages (ps: with ps; [
    flask
    ps."flask-wtf"  # CSRF protection
    mnemonic  # BIP39 mnemonic generation
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "lnbitspi-configurator";
  version = "1.0.0";

  src = ./configurator-app;

  dontBuild = true;

  installPhase = ''
    mkdir -p $out/lib/lnbitspi-configurator
    mkdir -p $out/bin

    # Copy application files
    cp -r $src/* $out/lib/lnbitspi-configurator/

    # Create wrapper script
    cat > $out/bin/lnbitspi-configurator << EOF
#!/usr/bin/env bash
set -euo pipefail

cd $out/lib/lnbitspi-configurator
exec ${python}/bin/python app.py "\$@"
EOF

    chmod +x $out/bin/lnbitspi-configurator
  '';

  meta = with pkgs.lib; {
    description = "LNbitsBox first-run setup wizard";
    license = pkgs.lib.licenses.mit;
    platforms = pkgs.lib.platforms.linux;
  };
}
