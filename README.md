# LNbits NixOS Raspberry Pi 4 image (Ethernet)

This repo builds a flashable NixOS SD-card image for Raspberry Pi 4 that runs LNbits as a systemd service.

## Download and flash

1. Go to **Releases** and download the latest `*.img.zst` and `SHA256SUMS.txt`
2. Flash the image to an SD card:
   - Raspberry Pi Imager (recommended), or
   - `zstd -d` then `dd` on Linux/macOS

Example on Linux/macOS (be careful with the disk name):

```bash
zstd -d lnbits-nixos-pi4-*.img.zst -o image.img
sudo dd if=image.img of=/dev/rdiskX bs=8m conv=sync status=progress