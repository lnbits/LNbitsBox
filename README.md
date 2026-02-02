# LNbits NixOS Raspberry Pi 4 Image

A pre-configured, bootable NixOS SD card image for Raspberry Pi 4 that runs [LNbits](https://github.com/lnbits/lnbits) as a systemd service.

## What's included

- **NixOS 24.11** (latest stable)
- **LNbits** running as a systemd service on port 9000
- **SSH enabled** for remote access
- **Mainline Linux kernel** (cached, no compilation needed)
- **Raspberry Pi 4 optimizations** (64-bit, UART enabled)
- **Firewall configured** (port 9000 open for LNbits)
- **Default user:** `lnbitsadmin` / password: `lnbits` (⚠️ change on first boot!)

## Quick start: Download and flash

1. Go to **[Releases](../../releases)** and download the latest `*.img.zst` and `SHA256SUMS.txt`
2. Verify the checksum:
   ```bash
   sha256sum -c SHA256SUMS.txt
   ```
3. Flash the image to an SD card:
   - **Raspberry Pi Imager** (recommended - auto-decompresses)
   - Or use command-line tools (see examples below)

**Example on Linux/macOS:**

```bash
# Option 1: Decompress and write in one command
zstd -dc lnbits-nixos-pi4-*.img.zst | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync

# Option 2: Decompress first, then write
zstd -d lnbits-nixos-pi4-*.img.zst -o image.img
sudo dd if=image.img of=/dev/sdX bs=4M status=progress conv=fsync
```

⚠️ Replace `/dev/sdX` with your actual SD card device. Use `lsblk` to find it.

4. Boot your Pi 4, find its IP address, and access LNbits at `http://<pi-ip>:9000`

# Build from source

To build the image yourself, follow these instructions for Debian/Ubuntu systems.

## **0) Prep a Debian / Ubuntu system**

Update and install required packages:

```bash
sudo apt update
sudo apt install -y curl git xz-utils zstd ca-certificates qemu-user-static binfmt-support
```

**System Requirements:**
- At least **20–30 GB free disk space**
- **4–8 GB RAM** (or add swap as shown below)
- x86_64 system (will use QEMU to emulate aarch64)

**Optional: Add swap** (recommended for systems with less than 8GB RAM):

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```


## **1) Install Nix and enable flakes**

Install Nix (multi-user daemon mode):

```bash
sh <(curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix) --daemon --yes
```

Or use the official installer:

```bash
sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --daemon --yes
```

Enable experimental features (flakes and nix-command):

```bash
sudo mkdir -p /etc/nix
echo 'experimental-features = nix-command flakes' | sudo tee -a /etc/nix/nix.conf
```

Restart the Nix daemon:

```bash
sudo systemctl restart nix-daemon
```

Load Nix into your current shell:

```bash
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

**Tip:** Add the above line to your `~/.bashrc` to make it permanent:

```bash
echo '. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' >> ~/.bashrc
```


## **2) Configure aarch64 cross-compilation**

Enable aarch64 builds in Nix configuration:

```bash
echo 'extra-platforms = aarch64-linux' | sudo tee -a /etc/nix/nix.conf
```

Restart the Nix daemon:

```bash
sudo systemctl restart nix-daemon
```

Verify the configuration:

```bash
nix show-config | grep extra-platforms
```

You should see `aarch64-linux` in the output.

**Note:** QEMU user emulation (qemu-user-static) was already installed in step 0. This allows your x86_64 system to build for aarch64 architecture.

## **3) Set up binary caches (recommended)**

Using Cachix will significantly speed up builds by downloading pre-built packages:

```bash
# Install Cachix
nix-env -iA cachix -f https://cachix.org/api/v1/install
```

Enable the binary caches:

```bash
cachix use nix-community
cachix use lnbits
cachix use raspberry-pi-nix
```

## **4) Clone the repo and build the SD image**

Clone the repository:

```bash
git clone https://github.com/blackcoffeexbt/lnbitspi
cd lnbitspi
```

Build the SD image:

```bash
nix build .#sdImage -L
```

The `-L` flag shows build logs in real-time. The build may take 30-60 minutes depending on your system and what needs to be built.

Check the result:

```bash
ls -lah result/sd-image/
```

You should see a `*.img.zst` file.

Copy the image to a distribution directory:

```bash
mkdir -p dist
cp -v result/sd-image/*.img.zst dist/
sha256sum dist/*.img.zst > dist/SHA256SUMS.txt
```

## **5) Verify the image**

Test that the image file is valid:

```bash
file dist/*.img.zst
zstd -t dist/*.img.zst
```

The first command should show it's a Zstandard compressed data file, and the second should complete without errors.

## **6) Flash to SD card**

Flash using **Raspberry Pi Imager** (recommended) or use command-line tools:

**On Linux/macOS:**

```bash
# Decompress and write in one command (replace /dev/sdX with your SD card device)
zstd -dc dist/*.img.zst | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

**Or decompress first, then write:**

```bash
zstd -d dist/*.img.zst -o image.img
sudo dd if=image.img of=/dev/sdX bs=4M status=progress conv=fsync
```

⚠️ **Warning:** Double-check the device name! Using the wrong device will destroy data.

## First boot

After flashing and booting the Raspberry Pi 4:

1. The Pi will automatically connect via DHCP
2. SSH is enabled by default
3. Login: `lnbitsadmin` / password: `lnbits`
4. LNbits will be running on port 9000
5. **Change the default password immediately after first login!**

```bash
ssh lnbitsadmin@<pi-ip-address>
passwd  # Change your password
```

Access LNbits at: `http://<pi-ip-address>:9000`

## Troubleshooting

**Build is slow:** Building on x86_64 with QEMU emulation can take time. Make sure you've enabled the Cachix binary caches (step 3) to download pre-built packages instead of building from source. If you have access to a native aarch64 machine, building there will be much faster.

**Out of disk space:** Ensure you have at least 20-30 GB free. Nix builds use significant temporary space.

**Out of memory:** Add swap space as shown in step 0, or use a machine with more RAM.

**Kernel build from source:** If you see the kernel being built from source, ensure you've added the `raspberry-pi-nix` Cachix cache and that your flake is using the mainline kernel override.

## Development

To modify the configuration:

1. Edit `nixos/configuration.nix` for system settings
2. Edit `nixos/lnbits-service.nix` for LNbits-specific configuration
3. Edit `flake.nix` to update dependencies or kernel settings

After making changes:

```bash
nix flake lock              # Update dependencies if needed
nix build .#sdImage -L      # Build new image
```

## Project structure

```
.
├── flake.nix                    # Main flake definition
├── flake.lock                   # Locked dependency versions
├── nixos/
│   ├── configuration.nix        # Main NixOS configuration
│   └── lnbits-service.nix      # LNbits systemd service definition
└── .github/workflows/
    └── build-image.yml          # GitHub Actions CI/CD
```

## License

This project configuration is provided as-is for educational and deployment purposes. LNbits itself is licensed under the MIT License.
