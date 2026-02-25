{ pkgs }:

let
  python = pkgs.python3.withPackages (ps: with ps; [
    flask
    ps."flask-wtf"  # CSRF protection
    psutil
    requests
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "lnbitspi-admin";
  version = "1.0.0";

  src = ./admin-app;

  dontBuild = true;

  installPhase = ''
    mkdir -p $out/lib/lnbitspi-admin
    mkdir -p $out/bin

    # Copy application files
    cp -r $src/* $out/lib/lnbitspi-admin/

    # Create wrapper script
    cat > $out/bin/lnbitspi-admin << EOF
#!${pkgs.bash}/bin/bash
set -euo pipefail

cd $out/lib/lnbitspi-admin
exec ${python}/bin/python app.py "\$@"
EOF

    chmod +x $out/bin/lnbitspi-admin
  '';

  meta = with pkgs.lib; {
    description = "LNbitsBox admin dashboard";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
