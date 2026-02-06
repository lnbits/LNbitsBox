{
  description = "NixOS Raspberry Pi 4 SD image running LNbits";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    # Raspberry Pi firmware + SD image module
    # Using main branch for better cache coverage
    raspberry-pi-nix.url = "github:nix-community/raspberry-pi-nix";
    raspberry-pi-nix.inputs.nixpkgs.follows = "nixpkgs";

    # LNbits flake input - using sparkwallet branch until merged into a release
    # To update: nix flake lock --update-input lnbits
    lnbits.url = "github:lnbits/lnbits/sparkwallet";

    # Spark sidecar for L2 Lightning integration
    spark-sidecar.url = "github:lnbits/spark_sidecar";
    spark-sidecar.flake = false;  # Not a flake, just source
  };

  outputs = { self, nixpkgs, raspberry-pi-nix, lnbits, spark-sidecar, ... }:
  let
    system = "aarch64-linux";
  in
  {
    # Compressed SD image (default, for releases)
    nixosConfigurations.pi4 = nixpkgs.lib.nixosSystem {
      inherit system;
      specialArgs = { inherit lnbits spark-sidecar; };
      modules = [
        raspberry-pi-nix.nixosModules.raspberry-pi
        raspberry-pi-nix.nixosModules.sd-image
        ./nixos/configuration.nix
        # Override to use mainline kernel instead of raspberry-pi kernel
        {
          boot.kernelPackages = nixpkgs.lib.mkForce nixpkgs.legacyPackages.${system}.linuxPackages_latest;
        }
      ];
    };

    # Uncompressed SD image (for faster local testing)
    nixosConfigurations.pi4-uncompressed = nixpkgs.lib.nixosSystem {
      inherit system;
      specialArgs = { inherit lnbits spark-sidecar; };
      modules = [
        raspberry-pi-nix.nixosModules.raspberry-pi
        raspberry-pi-nix.nixosModules.sd-image
        ./nixos/configuration.nix
        # Override to use mainline kernel instead of raspberry-pi kernel
        {
          boot.kernelPackages = nixpkgs.lib.mkForce nixpkgs.legacyPackages.${system}.linuxPackages_latest;
        }
        # Disable compression for faster testing
        {
          sdImage.compressImage = false;
        }
      ];
    };

    # Expose packages for x86_64-linux (cross-compilation)
    packages.x86_64-linux = {
      # Compressed SD image (default, for releases)
      sdImage = self.nixosConfigurations.pi4.config.system.build.sdImage;

      # Uncompressed SD image (for faster local testing)
      sdImageUncompressed = self.nixosConfigurations.pi4-uncompressed.config.system.build.sdImage;

      # Default to compressed
      default = self.nixosConfigurations.pi4.config.system.build.sdImage;
    };

    # Expose packages for aarch64-linux (native builds)
    packages.aarch64-linux = {
      # Compressed SD image (default, for releases)
      sdImage = self.nixosConfigurations.pi4.config.system.build.sdImage;

      # Uncompressed SD image (for faster local testing)
      sdImageUncompressed = self.nixosConfigurations.pi4-uncompressed.config.system.build.sdImage;

      # Default to compressed
      default = self.nixosConfigurations.pi4.config.system.build.sdImage;
    };
  };
}