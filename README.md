# LNbits NixOS Raspberry Pi 4 Image

A pre-configured, bootable NixOS SD card image for Raspberry Pi 4 that runs [LNbits](https://github.com/lnbits/lnbits) as a systemd service.

## What's included

- **NixOS 24.11** (latest stable)
- **LNbits v1.4.2** running as a systemd service on port 80
- **Spark L2 Lightning sidecar** for advanced wallet features
- **First-run configuration wizard** for easy setup
- **SSH enabled** for remote access
- **Mainline Linux kernel** (cached, no compilation needed)
- **Raspberry Pi 4 optimizations** (64-bit, UART enabled)
- **Tor hidden service** for private remote access (`.onion` address, no port forwarding needed)
- **nginx reverse proxy** for secure internal routing
- **Firewall configured** (port 80 open)

### SD Card Partition Layout

After flashing, your SD card will have two partitions:

1. **FIRMWARE** (FAT32, ~100MB) - Boot partition with Raspberry Pi firmware, kernel, and config.txt
2. **NIXOS_SD** (ext4, remaining space) - Root filesystem with the full NixOS system

You can customize the firmware partition label by setting `raspberry-pi-nix.firmware-partition-label` in `nixos/configuration.nix`.

### Directory Structure

Once configured, the system uses the following directories:

- **`/var/lib/lnbits`** - LNbits data directory (database, uploaded files, etc.)
- **`/var/lib/lnbits-extensions`** - Extensions/plugins directory
- **`/var/lib/spark-sidecar`** - Spark wallet data and mnemonic
- **`/var/lib/tor/onion/lnbits`** - Tor hidden service keys and hostname
- **`/etc/lnbits/lnbits.env`** - LNbits configuration file

All directories are owned by their respective system users and persist across reboots.

## Quick start: Download and flash

### Step 1: Download the image

1. Go to **[Releases](../../releases)**
2. Download the latest `nixos-sd-image-*-aarch64-linux.img.zst` file
3. (Optional) Download `SHA256SUMS.txt` to verify integrity

### Step 2: Flash to SD card

Choose your preferred method based on your operating system:

#### **Method 1: Raspberry Pi Imager (Easiest - All Platforms)**

**Recommended for most users** - Works on Windows, macOS, and Linux.

1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your SD card (16GB minimum recommended)
3. Open Raspberry Pi Imager
4. Click **"Choose OS"** → Scroll down → **"Use custom"**
5. Select your downloaded `*.img.zst` file (no need to decompress!)
6. Click **"Choose Storage"** and select your SD card
7. Click **"Write"** and wait for completion

✅ Raspberry Pi Imager automatically decompresses `.zst` files!

#### **Method 2: balenaEtcher (Easy - All Platforms)**

Another user-friendly option that works on Windows, macOS, and Linux.

1. Download and install [balenaEtcher](https://etcher.balena.io/)
2. You'll need to **decompress the image first**:
   - **Windows:** Use [7-Zip](https://www.7-zip.org/) or [PeaZip](https://peazip.github.io/)
   - **macOS/Linux:** Run `zstd -d nixos-sd-image-*.img.zst` in terminal
3. Open balenaEtcher
4. Click **"Flash from file"** and select the decompressed `.img` file
5. Click **"Select target"** and choose your SD card
6. Click **"Flash!"**

#### **Method 3: Command Line (Advanced Users)**

**Linux:**
```bash
# Option A: Decompress and write in one command
zstd -dc nixos-sd-image-*.img.zst | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync

# Option B: Decompress first, then write
zstd -d nixos-sd-image-*.img.zst
sudo dd if=nixos-sd-image-*.img of=/dev/sdX bs=4M status=progress conv=fsync
```

**macOS:**
```bash
# Find your SD card device (look for /dev/diskX)
diskutil list

# Unmount the SD card (replace diskX with your device)
diskutil unmountDisk /dev/diskX

# Write the image (use rdiskX for faster writing)
zstd -dc nixos-sd-image-*.img.zst | sudo dd of=/dev/rdiskX bs=4m

# Eject when complete
diskutil eject /dev/diskX
```

**Windows (PowerShell as Administrator):**
```powershell
# Install zstd if you don't have it
# Download from: https://github.com/facebook/zstd/releases

# Decompress
zstd -d nixos-sd-image-*.img.zst

# Use Rufus, Win32DiskImager, or dd for Windows to write the .img file
```

⚠️ **Warning:** Double-check your device name! Writing to the wrong device will destroy data.
- Linux: Use `lsblk` to identify your SD card
- macOS: Use `diskutil list` to identify your SD card
- Windows: Check in Disk Management

### Step 3: First boot

1. Insert the SD card into your Raspberry Pi 4
2. Connect ethernet cable (or configure WiFi later)
3. Power on the Pi
4. **If you have a monitor connected:**
   - You'll see boot messages and a login prompt
   - The system displays a welcome message with setup instructions
5. Wait 2-3 minutes for first boot to complete
6. Find the Pi's IP address:
   - Check your router's DHCP client list for hostname `lnbits`
   - Try connecting via mDNS: `ssh lnbitsadmin@lnbits.local`
   - Use a network scanner like `nmap` or `angry-ip-scanner`
   - Or check the login screen if you have a monitor connected

### Step 4: Complete the setup wizard

On first boot, LNbitsBox presents a configuration wizard at `http://<pi-ip-address>/`

**Open your browser:**
```
http://<pi-ip-address>/
```

**Follow the wizard steps:**

1. **Generate or import Spark wallet seed**
   - Click "Generate New Seed Phrase" for a new 12-word BIP39 mnemonic
   - OR paste an existing seed phrase to import
   - ⚠️ **CRITICAL:** Write down your seed phrase and store it safely
   - You will only see it once during this setup
   - Check the box confirming you've saved it

2. **Set SSH password**
   - Create a password for the `lnbitsadmin` user
   - Minimum 8 characters
   - You'll use this to SSH into your Pi

3. **Complete setup**
   - The wizard will configure your system
   - Wait 10-15 seconds for services to start
   - LNbits will open automatically

### Step 5: Access LNbits

After completing the wizard, LNbits is available at the same URL:

```
http://<pi-ip-address>/
```

**SSH access:**
```bash
ssh lnbitsadmin@<pi-ip-address>
# Use the password you set in the wizard
```

**Tor access (remote/private):**

LNbits is also available as a Tor hidden service. The `.onion` address is generated automatically on first boot (takes 1-2 minutes). You can find it:
- In the admin dashboard at `https://<pi-ip-address>/box/` (shown in the Tor Address card)
- Via SSH: `cat /var/lib/tor/onion/lnbits/hostname`

To access LNbits over Tor, open the `.onion` URL in [Tor Browser](https://www.torproject.org/download/). This works from anywhere without port forwarding.

That's it! Your LNbits node with Spark L2 Lightning is now running.

## Resetting the configuration

If you need to re-run the setup wizard (for example, if you skipped saving the seed phrase):

**SSH into your Pi:**
```bash
ssh lnbitsadmin@<pi-ip-address>
```

**Run the reset command:**
```bash
sudo lnbitspi-reset
```

This will:
- Stop LNbits and Spark sidecar services
- Remove the configuration marker
- Optionally delete the Spark mnemonic (you'll be prompted)
- Re-enable the setup wizard

After reset, the wizard will be available again at `http://<pi-ip-address>/`

⚠️ **Note:** This does NOT delete your LNbits database or user data.

# Build from source

To build the image yourself, follow these instructions for Debian/Ubuntu systems.

## Build Options

You can build two variants of the SD image:

| Build Type | Command | Output | Use Case |
|------------|---------|--------|----------|
| **Compressed** (default) | `nix build .#sdImage -L` | `*.img.zst` | For distribution, GitHub releases (smaller file size) |
| **Uncompressed** | `nix build .#sdImageUncompressed -L` | `*.img` | For local testing (faster build, faster flashing) |
| **Quick Test** | `./build-test.sh` | `*.img` (copied to repo root) | Fastest way to build and prepare for flashing |

**Recommendation:** Use `./build-test.sh` during development for fastest iteration. It builds uncompressed and copies the image to the repo root for easy access.

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

## Troubleshooting

### Flashing Issues

**"Not enough space" error:**
- Ensure your SD card is at least 8GB (16GB+ recommended)
- Some SD cards report less usable space than advertised

**Image won't decompress:**
- **Windows:** Install [7-Zip](https://www.7-zip.org/) or [PeaZip](https://peazip.github.io/)
- **macOS:** Install zstd: `brew install zstd`
- **Linux:** Install zstd: `sudo apt install zstd` or `sudo yum install zstd`

**"Permission denied" when flashing:**
- Linux/macOS: Use `sudo` with dd commands
- Windows: Run as Administrator
- Make sure the SD card is not mounted/in use

**Flashing fails or SD card not detected:**
- Try a different SD card (some old/cheap cards have compatibility issues)
- Use a different SD card reader
- Check if the SD card is write-protected (physical switch on some cards)

### Boot Issues

**Screen goes black after boot messages:**
- **By default, this is expected behavior** - the system is configured for SSH access only
- After showing "Reached target multi-user system", the display goes blank
- The system is running fine and waiting for SSH connections
- To verify: Check your router for the Pi's IP address or try `ssh lnbitsadmin@lnbits-pi4.local`
- **To enable console login on HDMI**, the configuration needs these kernel parameters in `nixos/configuration.nix`:
  ```nix
  boot.kernelParams = [
    "consoleblank=0"
    "console=tty1"  # Force console to HDMI (otherwise it goes to serial UART)
  ];
  systemd.services."getty@tty1".enable = true;
  ```
  The latest version already has these enabled. If using an older image, rebuild and reflash with the latest code.

**Pi won't boot / No activity at all:**
- Verify the image was written completely (check file sizes)
- Try re-flashing the image
- Ensure you're using a Raspberry Pi 4 (this image won't work on Pi 3 or earlier)
- Check your power supply (Pi 4 needs a good 5V/3A USB-C supply)
- Look for the green activity LED - it should blink during boot

**Boot messages stop or system hangs before "multi-user system":**
- This indicates an actual boot problem (different from black screen above)
- Connect via serial console (UART pins) to see detailed logs
- Check if you modified any critical system settings
- Try reflashing with the official unmodified image first

**Can't find the Pi's IP address:**
- Wait 3-5 minutes for first boot (it takes longer than subsequent boots)
- Check your router's connected devices list
- Connect a monitor and keyboard to see boot messages and login directly
- Try connecting via ethernet instead of WiFi (WiFi needs additional configuration)

**Can't SSH into the Pi:**
- Make sure you're on the same network
- Try `ssh -v lnbitsadmin@<ip>` for verbose debugging
- Check if port 22 is open: `nmap -p 22 <ip>`
- Wait a bit longer - first boot takes time

**Can't access web interface (wizard or LNbits):**
- Verify nginx is running: `ssh` into the Pi and run `systemctl status nginx`
- Check if port 80 is open: `nmap -p 80 <ip>`
- Try accessing from a different device on the same network
- Check firewall rules: `sudo iptables -L -n | grep 80`
- If configured, check LNbits is running: `systemctl status lnbits`
- If not configured, check configurator is running: `systemctl status lnbitspi-configurator`

**Wizard doesn't appear on first boot:**
- Wait a few minutes for the configurator service to start
- Check if configurator is running: `ssh` into Pi and run `systemctl status lnbitspi-configurator`
- Check nginx is routing correctly: `curl -I http://localhost/`
- If already configured, the marker file exists: `ls /var/lib/lnbits/.configured`
- To re-run wizard, use: `sudo lnbitspi-reset`

**Can't set SSH password in wizard:**
- Ensure you're entering at least 8 characters
- Check passwords match exactly
- If it fails, check logs: `journalctl -u lnbitspi-configurator`

**Services don't start after wizard:**
- Wait 10-15 seconds for services to start
- Check spark-sidecar: `systemctl status spark-sidecar`
- Check lnbits: `systemctl status lnbits`
- Check logs: `journalctl -u spark-sidecar` and `journalctl -u lnbits`
- Verify marker file exists: `ls /var/lib/lnbits/.configured`

**Forgot to save seed phrase:**
- Run `sudo lnbitspi-reset` to restart the wizard
- Choose NOT to delete the mnemonic when prompted
- In the wizard, import your existing mnemonic instead of generating new

**Tor hidden service not working / no `.onion` address:**
- Tor takes 1-2 minutes to establish the hidden service on first boot
- Check Tor is running: `systemctl status tor`
- Check Tor logs: `journalctl -u tor`
- Verify the hostname file exists: `sudo cat /var/lib/tor/onion/lnbits/hostname`
- The `.onion` address persists across reboots once generated

**LNbits can't connect to Spark sidecar:**
- Check Spark is running: `systemctl status spark-sidecar`
- Check Spark logs: `journalctl -u spark-sidecar`
- Verify mnemonic file exists: `sudo ls -l /var/lib/spark-sidecar/mnemonic`
- Check LNbits config has Spark URL: `cat /etc/lnbits/lnbits.env | grep SPARK`

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

## License

This project configuration is provided as-is for educational and deployment purposes. LNbits itself is licensed under the MIT License.


