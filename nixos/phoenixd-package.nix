{ pkgs }:

let
  version = "0.7.3";
in
pkgs.stdenv.mkDerivation {
  pname = "phoenixd";
  inherit version;

  src = pkgs.fetchzip {
    url = "https://github.com/ACINQ/phoenixd/releases/download/v${version}/phoenixd-${version}-linux-arm64.zip";
    hash = "sha256-ZHMgR+WwBRBsPRV9hK8bjvluvsxIf8o/CKIDWu7gH7g=";
    stripRoot = false;
  };

  nativeBuildInputs = [ pkgs.autoPatchelfHook ];
  buildInputs = [
    pkgs.libxcrypt-legacy
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    install -Dm0755 phoenixd-${version}-linux-arm64/phoenixd $out/bin/phoenixd
    install -Dm0755 phoenixd-${version}-linux-arm64/phoenix-cli $out/bin/phoenix-cli

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Minimal self-custodial Lightning node with an HTTP API";
    homepage = "https://github.com/ACINQ/phoenixd";
    license = licenses.asl20;
    platforms = [ "aarch64-linux" ];
  };
}
