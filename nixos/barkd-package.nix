{ pkgs, bark, fenix }:

let
  rust = fenix.packages.${pkgs.system}.fromToolchainName {
    name = "1.90.0";
    sha256 = "sha256-SJwZ8g0zF2WrKDVmHrVG3pD2RGoQeo24MEXnNx5FyuI=";
  };
  rustPlatform = pkgs.makeRustPlatform {
    cargo = rust.cargo;
    # Fenix toolchains bundle rustc and cargo in one derivation. nixpkgs 24.11
    # expects rustc.targetPlatforms, which the bundled derivation omits.
    rustc = rust.rustc // {
      targetPlatforms = pkgs.lib.platforms.all;
      badTargetPlatforms = [];
    };
  };
in
rustPlatform.buildRustPackage {
  pname = "barkd";
  version = "0.4.0";
  src = bark;

  cargoHash = pkgs.lib.fakeHash;

  nativeBuildInputs = [ pkgs.pkg-config pkgs.protobuf ];
  buildInputs = [ pkgs.openssl pkgs.sqlite ];

  cargoBuildFlags = [ "-p" "bark-cli" "--bin" "bark" "--bin" "barkd" ];
  cargoTestFlags = [ "-p" "bark-cli" "--no-run" ];

  meta = {
    description = "Bark and barkd wallet binaries";
    homepage = "https://gitlab.com/ark-bitcoin/bark";
    license = pkgs.lib.licenses.mit;
    mainProgram = "barkd";
  };
}
