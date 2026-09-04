{ pkgs, bark, fenix }:

let
  swaggerUi = pkgs.fetchurl {
    url = "https://github.com/swagger-api/swagger-ui/archive/refs/tags/v5.17.14.zip";
    hash = "sha256-SBJE0IEgl7Efuu73n3HZQrFxYX+cn5UU5jrL4T5xzNw=";
  };
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
  cargoDepsBase = rustPlatform.importCargoLock {
    lockFile = "${bark}/Cargo.lock";
    extraRegistries = {
      "https://github.com/rust-lang/crates.io-index" = "https://static.crates.io/crates";
    };
  };
  cargoDeps = pkgs.runCommand "barkd-cargo-deps" { } ''
    cp -r ${cargoDepsBase} $out
    chmod -R u+w $out
    sed -i '\#^\[source\."https://github.com/rust-lang/crates.io-index"\]$#,+3d' $out/.cargo/config.toml
    sed -i 's#directory = "cargo-vendor-dir"#directory = "barkd-cargo-deps"#' $out/.cargo/config.toml
  '';
in
rustPlatform.buildRustPackage {
  pname = "barkd";
  version = "0.4.0";
  src = bark;

  # Bark's lockfile has only registry dependencies, so Nix can fetch each
  # locked crate directly. This avoids a manually maintained vendor hash.
  cargoDeps = cargoDeps;
  doCheck = false;

  nativeBuildInputs = [ pkgs.pkg-config pkgs.protobuf pkgs.curl ];
  buildInputs = [ pkgs.openssl pkgs.sqlite ];

  # utoipa-swagger-ui normally downloads this archive in its build script.
  # Give it a fixed local Nix store path instead: Nix sandbox builds have no
  # network access, and the resulting barkd binary still includes Swagger UI.
  SWAGGER_UI_DOWNLOAD_URL = "file://${swaggerUi}";

  cargoBuildFlags = [ "-p" "bark-cli" "--bin" "bark" "--bin" "barkd" ];
  cargoTestFlags = [ "-p" "bark-cli" "--no-run" ];

  meta = {
    description = "Bark and barkd wallet binaries";
    homepage = "https://gitlab.com/ark-bitcoin/bark";
    license = pkgs.lib.licenses.mit;
    mainProgram = "barkd";
  };
}
