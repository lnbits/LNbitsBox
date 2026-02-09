# Build from source

To build the image yourself, follow these instructions for Debian/Ubuntu systems.

## Build Options

You can build two variants of the SD image:

| Build Type | Command | Output | Use Case |
|------------|---------|--------|----------|
| **Compressed** (default) | `nix build .#sdImage -L` | `*.img.zst` | For distribution, GitHub releases (smaller file size) |
| **Uncompressed** | `nix build .#sdImageUncompressed -L` | `*.img` | For local testing (faster build, faster flashing) |
| **Quick Test** | `./build-test.sh` | `*.img` (copied to repo root) | Fastest way to build and prepare for flashing |

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
sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install)
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
cachix use raspberry-pi-nix
```

**Note:** The standard nixpkgs cache is already enabled by default and provides most packages including LNbits dependencies.

## **4) Clone the repo and build the SD image**

Clone the repository:

```bash
git clone https://github.com/blackcoffeexbt/lnbitspi
cd lnbitspi
```

Build the SD image:

```bash
# Quick test build (recommended for development)
# Builds uncompressed and copies to repo root
./build-test.sh

# OR: Manual builds
# Compressed image (default, smaller for distribution)
nix build .#sdImage -L

# Uncompressed image (faster for local testing, skips compression)
nix build .#sdImageUncompressed -L
```

The `-L` flag shows build logs in real-time. The build may take 30-60 minutes depending on your system and what needs to be built.

**Note:** The uncompressed build is significantly faster because it skips the zstd compression step (saves ~5-10 minutes). The `build-test.sh` script automatically copies the image to the repo root for easy flashing.

Check the result:

```bash
ls -lah result/sd-image/
```

You should see:
- **Compressed build:** `*.img.zst` file in `result/sd-image/`
- **Uncompressed build:** `*.img` file in `result/sd-image/`
- **Quick test build:** `*.img` file in repo root (ready to flash)

Copy the image to a distribution directory:

```bash
mkdir -p dist

# For compressed images (releases)
cp -v result/sd-image/*.img.zst dist/
sha256sum dist/*.img.zst > dist/SHA256SUMS.txt

# For uncompressed images (if using build-test.sh, already in repo root)
cp -v *.img dist/
sha256sum dist/*.img > dist/SHA256SUMS.txt
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
# For COMPRESSED images (.img.zst):
# Decompress and write in one command (replace /dev/sdX with your SD card device)
zstd -dc dist/*.img.zst | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync

# For UNCOMPRESSED images (.img) - faster, no decompression needed:
sudo dd if=dist/*.img of=/dev/sdX bs=4M status=progress conv=fsync
```

**Or decompress first, then write (compressed only):**

```bash
zstd -d dist/*.img.zst -o image.img
sudo dd if=image.img of=/dev/sdX bs=4M status=progress conv=fsync
```

⚠️ **Warning:** Double-check the device name! Using the wrong device will destroy data.

## First boot

After flashing and booting the Raspberry Pi 4:

1. The Pi will automatically connect via DHCP
2. Navigate to `http://<pi-ip-address>/` to access the setup wizard
3. Complete the wizard to:
   - Generate/import your Spark wallet seed
   - Set SSH password for `lnbitsadmin` user
   - Configure and start LNbits

After setup is complete, access LNbits at: `http://<pi-ip-address>/`

### Build Issues (For developers)

**Build is slow:** Building on x86_64 with QEMU emulation can take time. Make sure you've enabled the Cachix binary caches (step 3) to download pre-built packages instead of building from source. If you have access to a native aarch64 machine, building there will be much faster.

**Out of disk space:** Ensure you have at least 20-30 GB free. Nix builds use significant temporary space.

**Out of memory:** Add swap space as shown in step 0, or use a machine with more RAM.

**Kernel build from source:** If you see the kernel being built from source, ensure you've added the `raspberry-pi-nix` Cachix cache and that your flake is using the mainline kernel override.

### Getting Help

If you're still having issues:
1. Check the [Issues](../../issues) page for similar problems
2. Create a new issue with details about your setup and error messages
3. Include the output of `systemctl status lnbits` if the Pi boots but LNbits isn't working

## Development

### Updating LNbits version

The LNbits version is pinned in `flake.nix`. To change versions:

**Pin to a specific stable release (recommended):**
```nix
# In flake.nix, change:
lnbits.url = "github:lnbits/lnbits/v1.4.2";
```

Available versions: Check [LNbits releases](https://github.com/lnbits/lnbits/releases)

**Other pinning options:**
```nix
# Latest stable release (tracks main branch - may break)
lnbits.url = "github:lnbits/lnbits";

# Specific commit SHA
lnbits.url = "github:lnbits/lnbits/abc123def456...";

# Specific branch
lnbits.url = "github:lnbits/lnbits/dev";
```

**After changing the version:**
```bash
nix flake lock --update-input lnbits  # Update just LNbits
nix build .#sdImage -L                # Build new image
```

### Changing default username/password

The default SSH credentials are defined in `nixos/configuration.nix`:

**Change the username:**
```nix
# Change "lnbitsadmin" to your desired username
users.users.myusername = {
  isNormalUser = true;
  extraGroups = [ "wheel" ];
  initialPassword = "mypassword";
};
```

**Change the password (Method 1 - Simple):**
```nix
users.users.lnbitsadmin = {
  isNormalUser = true;
  extraGroups = [ "wheel" ];
  initialPassword = "your-new-password";  # Change this
};
```
⚠️ Note: `initialPassword` is stored in plaintext in `/nix/store`

**Change the password (Method 2 - More secure):**

Generate a hashed password:
```bash
# On any Linux system with mkpasswd:
mkpasswd -m yescrypt
# Enter your desired password when prompted
```

Then use the hash in your configuration:
```nix
users.users.lnbitsadmin = {
  isNormalUser = true;
  extraGroups = [ "wheel" ];
  # hashedPassword = "$y$j9T$...paste-hash-here...";
  initialPassword = null;  # Remove initialPassword when using hashedPassword
};
```

After changing username/password, rebuild the image:
```bash
nix build .#sdImage -L
```

### Modifying system configuration

To modify other aspects of the system:

1. Edit `nixos/configuration.nix` for system settings (users, networking, packages)
2. Edit `nixos/lnbits-service.nix` for LNbits-specific configuration (port, environment)
3. Edit `flake.nix` to update dependencies or kernel settings

After making changes:

```bash
nix flake lock              # Update all dependencies (if needed)
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

# Configuration App

The configuration app is a web application that runs on first boot to guide users through the initial setup process. It handles:
- Generating or importing the Spark wallet seed phrase
- Setting the SSH password for the `lnbitsadmin` user
- Starting the LNbits and Spark services after configuration is complete.

To run the app locally for development:
```bash
cd nixos/configurator-app
python3 -m venv venv
source venv/bin/activate
pip install mnemonic
export DEV_MODE=true
python3 app.py
```