# OTA System Updates

LNbitsBox supports over-the-air system updates so users don't need to reflash their SD card for new releases. This works by leveraging NixOS's immutable store and a Cachix binary cache — CI builds the full system closure, pushes it to Cachix, and the Pi downloads and activates it directly. Zero compilation on the Pi.

## How It Works

```
CI (GitHub Actions)                        Pi (NixOS)
┌──────────────────────┐                  ┌──────────────────────┐
│ Build system toplevel│                  │ Admin app checks     │
│ Push to Cachix cache │                  │ GitHub Releases API  │
│ Upload manifest.json │                  │ for new versions     │
│ to GitHub Release    │                  │                      │
└──────────────────────┘                  │ Download closure     │
                                          │ from Cachix          │
                                          │ Activate new system  │
                                          └──────────────────────┘
```

1. **CI builds** the NixOS system toplevel (`nix build .#toplevel`) — this is the entire system closure (kernel, services, config, everything).
2. **CI pushes** the closure to the `lnbitsbox` Cachix binary cache so it can be downloaded without rebuilding.
3. **CI uploads** a `manifest.json` to the GitHub Release containing the Nix store path and version.
4. **On the Pi**, the admin dashboard checks the GitHub Releases API for new versions.
5. When the user clicks "Update Now", the Pi downloads `manifest.json`, fetches the closure from Cachix via `nix copy`, and activates it with `switch-to-configuration switch`.

The key insight: the Pi never evaluates any Nix expressions. It just downloads pre-built binaries and switches to them.

## Prerequisites

Before OTA updates will work, you need a Cachix binary cache set up:

1. **Create a Cachix account** at https://cachix.org
2. **Create a cache** named `lnbitsbox` (or choose another name and update the references)
3. **Note the public signing key** — it looks like `lnbitsbox.cachix.org-1:XXXXXXXX...`
4. **Update `nixos/configuration.nix`** — replace `<PUBLIC_KEY_HERE>` with your cache's public key:
   ```nix
   trusted-public-keys = [
     "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
     "lnbitsbox.cachix.org-1:YOUR_ACTUAL_PUBLIC_KEY_HERE"
   ];
   ```
5. **Add the Cachix auth token as a GitHub secret** — go to your repo's Settings > Secrets and add `CACHIX_AUTH_TOKEN` with the write token from your Cachix dashboard.

## Releasing a New Version

### Step 1: Bump the version

Edit `flake.nix` and update the version string:

```nix
let
  version = "1.1.0";  # Bump this
  system = "aarch64-linux";
in
```

### Step 2: Commit and tag

```bash
git add -A
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

### Step 3: CI does the rest

Pushing a `v*` tag triggers the `build-pi4-image` workflow (`.github/workflows/build-image.yml`), which:

1. Builds the compressed SD image (`nix build .#sdImage`)
2. Builds the system toplevel (`nix build .#toplevel`)
3. Pushes the toplevel closure to Cachix (`cachix push lnbitsbox result-toplevel`)
4. Creates `manifest.json` with the store path and version
5. Uploads the SD image, checksums, and `manifest.json` to a GitHub Release

After the workflow completes, any LNbitsBox running an older version will see the update available in the admin dashboard.

## CI Workflow Details

The relevant steps in `.github/workflows/build-image.yml`:

| Step | What it does |
|------|-------------|
| **Set up LNbitsBox Cachix** | Configures Cachix with the `CACHIX_AUTH_TOKEN` secret for push access |
| **Build SD image** | `nix build .#sdImage -L --out-link result-sdimage` — full SD card image |
| **Build and push toplevel** | `nix build .#toplevel -L --out-link result-toplevel` then `cachix push` — the OTA closure |
| **Create update manifest** | Reads the store path and version, writes `manifest.json` |
| **Create GitHub Release** | Uploads `.img.zst`, `SHA256SUMS.txt`, and `manifest.json` |

The toplevel build and Cachix push use `continue-on-error: true` so that a Cachix misconfiguration won't block the SD image release.

## Manual Cachix Push (for developers)

If you need to push a build to Cachix manually (e.g., testing OTA without a full release cycle):

### Install Cachix

```bash
nix-env -iA cachix -f https://cachix.org/api/v1/install
```

### Authenticate

```bash
cachix authtoken <your-auth-token>
```

You can get your auth token from https://app.cachix.org (click your cache > Settings > Auth Tokens).

### Build and push the toplevel

```bash
# Build the system toplevel
nix build .#toplevel -L --out-link result-toplevel

# Push to the cache
cachix push lnbitsbox result-toplevel
```

This pushes the entire system closure (and all its dependencies) to the binary cache. The push only uploads store paths that aren't already in the cache, so subsequent pushes of similar builds are fast.

### Create a manifest manually

If you want to test the full OTA flow without a GitHub Release, you can create a `manifest.json` manually:

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

Then upload this `manifest.json` as a release asset (or serve it some other way for testing).

### Verify the push

You can verify the closure is available in the cache:

```bash
# Check if a specific store path is in the cache
nix path-info --store https://lnbitsbox.cachix.org $(readlink -f result-toplevel)
```

If this returns the path info without error, it's in the cache and ready for download.

## What Happens on the Pi

The update script (`nixos/update-service.nix`) runs these steps:

1. **Downloads `manifest.json`** from the GitHub Release URL
2. **Runs `nix-store --realise <store-path>`** to download the full system closure from all configured substituters (common packages like systemd come from `cache.nixos.org`, LNbitsBox-specific paths come from `lnbitsbox.cachix.org`)
3. **Runs `nix-env -p /nix/var/nix/profiles/system --set <store-path>`** to create a new system generation
4. **Runs `<store-path>/bin/switch-to-configuration switch`** to activate the new system

The update runs as a transient systemd unit (`lnbitsbox-update.service`) so it survives admin app restarts. Progress is written to `/var/lib/lnbitsbox-update/`:

| File | Contents |
|------|----------|
| `status` | `idle`, `downloading`, `activating`, `success`, or `failed` |
| `log` | Full output log with timestamps |
| `target-version` | The release tag being updated to |

The admin dashboard polls these files to show live progress to the user.

## File Overview

| File | Role |
|------|------|
| `flake.nix` | Defines `version`, exposes `.#toplevel` package |
| `nixos/configuration.nix` | Writes `/etc/lnbitsbox-version`, configures Cachix substituter and nix settings |
| `nixos/update-service.nix` | Update script, state directory, `lnbitsbox-update` command |
| `nixos/admin-app/app.py` | `/box/api/update/check`, `/start`, `/status` endpoints |
| `nixos/admin-app/templates/dashboard.html` | System Update UI card |
| `.github/workflows/build-image.yml` | Builds toplevel, pushes to Cachix, uploads manifest |

## Garbage Collection

Old system generations are automatically cleaned up weekly (configured in `configuration.nix`):

```nix
nix.gc = {
  automatic = true;
  dates = "weekly";
  options = "--delete-older-than 14d";
};
```

This prevents the Nix store from growing unbounded on the Pi's SD card. Generations older than 14 days are removed. The current and previous generation are always kept, allowing rollback.

## Troubleshooting

**"Cachix push failed" in CI**: Make sure `CACHIX_AUTH_TOKEN` is set as a GitHub repository secret and that the `lnbitsbox` cache exists on Cachix.

**Update check shows no update available**: The release must have a `manifest.json` asset. If CI's manifest step failed (e.g., Cachix wasn't configured), the admin app won't offer the update since there's no closure to download.

**Update fails with "Failed to download closure from Cachix"**: The public key in `configuration.nix` must match the Cachix cache's actual signing key. Also verify the Pi has internet access.

**Update fails during activation**: The `switch-to-configuration` step can fail if the new system has incompatible state. Check the full log at `/var/lib/lnbitsbox-update/log` on the Pi. The previous system generation is still intact — a reboot will boot into the last working generation.

**Testing locally with DEV_MODE**: Run the admin app with `DEV_MODE=true` and the update endpoints return mock data (update always available from v1.0.0 to v1.1.0). This lets you develop the UI without a real Cachix setup.
