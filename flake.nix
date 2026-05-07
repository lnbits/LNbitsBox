{
  description = "NixOS Raspberry Pi 4 SD image running LNbits";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    # Raspberry Pi firmware + SD image module
    # Using main branch for better cache coverage
    raspberry-pi-nix.url = "github:nix-community/raspberry-pi-nix";
    raspberry-pi-nix.inputs.nixpkgs.follows = "nixpkgs";

    # LNbits flake input - pinned to the Arkade funding-source branch until it lands upstream.
    # To update: nix flake lock --update-input lnbits
    lnbits.url = "github:blackcoffeexbt/lnbits/feat/arkade-funding-source";

    # Phoenixd source - build the JVM distribution from source on NixOS/aarch64.
    phoenixd.url = "github:ACINQ/phoenixd/v0.7.3";
    phoenixd.flake = false;

    # Spark sidecar for L2 Lightning integration
    spark-sidecar.url = "github:lnbits/spark_sidecar";
    spark-sidecar.flake = false;  # Not a flake, just source

    # Arkade sidecar for Ark funding-source integration
    arkade-sidecar.url = "github:lnbits/arkade_sidecar";
    arkade-sidecar.flake = false;
  };

  outputs = { self, nixpkgs, raspberry-pi-nix, lnbits, phoenixd, spark-sidecar, arkade-sidecar, ... }:
  let
    version = "0.9.8";  # Bump before each release tag to match the next tag name
    system = "aarch64-linux";
    mkPhoenixdPackage =
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      pkgs.callPackage ./nixos/phoenixd-package.nix { inherit phoenixd; };
  in
  {
    # Compressed SD image (default, for releases)
    nixosConfigurations.pi4 = nixpkgs.lib.nixosSystem {
      inherit system;
      specialArgs = { inherit lnbits phoenixd spark-sidecar arkade-sidecar version; };
      modules = [
        raspberry-pi-nix.nixosModules.raspberry-pi
        raspberry-pi-nix.nixosModules.sd-image
        ./nixos/configuration.nix
      ];
    };

    # Uncompressed SD image (for faster local testing)
    nixosConfigurations.pi4-uncompressed = nixpkgs.lib.nixosSystem {
      inherit system;
      specialArgs = { inherit lnbits phoenixd spark-sidecar arkade-sidecar version; };
      modules = [
        raspberry-pi-nix.nixosModules.raspberry-pi
        raspberry-pi-nix.nixosModules.sd-image
        ./nixos/configuration.nix
        # Disable compression for faster testing
        {
          sdImage.compressImage = false;
        }
      ];
    };

    # Expose packages for x86_64-linux (cross-compilation)
    packages.x86_64-linux = {
      phoenixd = mkPhoenixdPackage "x86_64-linux";

      # Compressed SD image (default, for releases)
      sdImage = self.nixosConfigurations.pi4.config.system.build.sdImage;

      # Uncompressed SD image (for faster local testing)
      sdImageUncompressed = self.nixosConfigurations.pi4-uncompressed.config.system.build.sdImage;

      # System toplevel (for OTA updates — CI builds and pushes to Cachix)
      toplevel = self.nixosConfigurations.pi4.config.system.build.toplevel;

      # Default to compressed
      default = self.nixosConfigurations.pi4.config.system.build.sdImage;
    };

    # Expose packages for aarch64-linux (native builds)
    packages.aarch64-linux = {
      phoenixd = mkPhoenixdPackage "aarch64-linux";

      # Compressed SD image (default, for releases)
      sdImage = self.nixosConfigurations.pi4.config.system.build.sdImage;

      # Uncompressed SD image (for faster local testing)
      sdImageUncompressed = self.nixosConfigurations.pi4-uncompressed.config.system.build.sdImage;

      # System toplevel (for OTA updates)
      toplevel = self.nixosConfigurations.pi4.config.system.build.toplevel;

      # Default to compressed
      default = self.nixosConfigurations.pi4.config.system.build.sdImage;
    };
  };
}
