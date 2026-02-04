{
  description = "NixOS Raspberry Pi 4 SD image running LNbits";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    # Raspberry Pi firmware + SD image module
    # Using main branch for better cache coverage
    raspberry-pi-nix.url = "github:nix-community/raspberry-pi-nix";
    raspberry-pi-nix.inputs.nixpkgs.follows = "nixpkgs";

    # LNbits flake input - pinned to v1.4.2 (latest stable)
    # To update: change the version tag and run: nix flake lock --update-input lnbits
    lnbits.url = "github:lnbits/lnbits/v1.4.2";
  };

  outputs = { self, nixpkgs, raspberry-pi-nix, lnbits, ... }:
  let
    system = "aarch64-linux";
  in
  {
    nixosConfigurations.pi4 = nixpkgs.lib.nixosSystem {
      inherit system;
      specialArgs = { inherit lnbits; };
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

    # Expose the SD image as a package for x86_64-linux
    packages.x86_64-linux.sdImage =
      self.nixosConfigurations.pi4.config.system.build.sdImage;

    packages.x86_64-linux.default =
      self.packages.x86_64-linux.sdImage;
  };
}