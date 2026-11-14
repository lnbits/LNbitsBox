{ pkgs, bark, fenix }:

let
  version = "0.8.1";
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
  inherit version;
  src = bark;

  # Bark's lockfile has only registry dependencies, so Nix can fetch each
  # locked crate directly. This avoids a manually maintained vendor hash.
  cargoDeps = cargoDeps;
  doCheck = false;

  nativeBuildInputs = [ pkgs.pkg-config pkgs.protobuf rustPlatform.bindgenHook ];
  buildInputs = [ pkgs.openssl pkgs.sqlite ];

  # Upstream build scripts use Git unless these release values are supplied.
  GIT_HASH = bark.rev;
  BARK_VERSION = version;

  # Swagger UI is now included in the upstream source behind an opt-in feature.
  cargoBuildFlags = [ "-p" "bark-cli" "--bin" "bark" "--bin" "bark-cli" "--bin" "barkd" "--features" "barkd-swagger-ui" ];
  cargoTestFlags = [ "-p" "bark-cli" "--no-run" ];

  meta = {
    description = "Bark CLI and barkd wallet binaries";
    homepage = "https://gitlab.com/ark-bitcoin/bark";
    license = pkgs.lib.licenses.mit;
    mainProgram = "barkd";
  };
}
