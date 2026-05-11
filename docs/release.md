# Release Guide

This guide covers manual release publishing for LNbitsBox, especially when the GitHub Actions release upload fails because the compressed SD image exceeds GitHub's per-asset size limit.

## When GitHub Actions fails with `size must be less than 2147483648`

GitHub Releases rejects any single uploaded asset larger than `2,147,483,648` bytes (2 GiB). If the workflow fails with:

```text
Validation Failed: {"resource":"ReleaseAsset","code":"custom","field":"size","message":"size must be less than 2147483648"}
```

the release upload step is failing because the `*.img.zst` file is too large.

You can still publish a working OTA release manually.

## What OTA updates actually need

For OTA updates, LNbitsBox only needs:

- The release tag, for example `v0.9.8`
- A `manifest.json` asset on that GitHub release
- The referenced Nix store closure pushed to `lnbitsbox.cachix.org`

The SD image is only needed for people doing a fresh manual flash. It is not required for OTA updates.

## Manual release workflow

### 1. Build and push the OTA system closure

```bash
nix build .#toplevel -L --out-link result-toplevel
cachix push lnbitsbox result-toplevel
```

This must succeed before publishing `manifest.json`, otherwise the device will see the update but fail to download the closure.

### 2. Create `manifest.json`

Use the exact `result-toplevel` you pushed to Cachix:

```bash
STORE_PATH=$(readlink -f result-toplevel)
VERSION=$(cat "$STORE_PATH/etc/lnbitsbox-version" 2>/dev/null || echo "unknown")

cat > manifest.json <<EOF
{
  "version": "$VERSION",
  "store_path": "$STORE_PATH",
  "nixos_version": "24.11"
}
EOF

cat manifest.json
```

Example:

```json
{
  "version": "0.9.8",
  "store_path": "/nix/store/ysm0wzyg69cnrgr8cnycdr2vymql8ki7-nixos-system-lnbits-24.11.20250630.50ab793",
  "nixos_version": "24.11"
}
```

Important:

- `version` should match the release version, such as `0.9.8`
- `store_path` must match the exact build that was pushed to Cachix
- Do not reuse an older manifest if you rebuilt `result-toplevel`

### 3. Optionally build the SD image and checksum

If you also want a manual flashing image:

```bash
nix build .#sdImageUncompressed -L --out-link result-sdimage
zstd -T0 --ultra -22 result-sdimage/sd-image/*.img -o lnbitsbox-0.9.8.img.zst
sha256sum lnbitsbox-0.9.8.img.zst > SHA256SUMS.txt
```

## What to upload to the GitHub release

### For OTA support

Upload:

- `manifest.json`

Optional but useful:

- `SHA256SUMS.txt`

### For fresh flashing

If the compressed SD image is under GitHub's size limit, you can also upload:

- `*.img.zst`

If the compressed SD image is over 2 GiB:

- Do not upload the `*.img.zst` asset to GitHub Releases
- Host it somewhere else
- Link to that external download from the release notes
- Upload `SHA256SUMS.txt` alongside it if the checksum applies to that image

## Recommended manual release contents

For a release where the image is too large for GitHub Releases:

- Upload `manifest.json`
- Upload `SHA256SUMS.txt`
- Add release notes explaining that OTA updates work normally
- Add a link to the externally hosted `*.img.zst` for fresh installs

## Verify the closure is in Cachix

Before publishing the manifest, verify the store path is available:

```bash
nix path-info --store https://lnbitsbox.cachix.org $(readlink -f result-toplevel)
```

If that command returns path information without error, the closure is available for OTA download.
