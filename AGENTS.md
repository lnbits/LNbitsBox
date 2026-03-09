# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

LNbitsBox is a bootable NixOS SD card image for Raspberry Pi 4 that runs LNbits with Lightspark Spark as a Lightning Network funding source. It includes a first-run configuration wizard, Tor hidden service, Wi-Fi config, admin dashboard, and OTA updates.

## Build Commands

```bash
# Compressed image (for GitHub releases)
nix build .#sdImage -L

# Uncompressed image (faster for local testing)
nix build .#sdImageUncompressed -L

# Quick test build — builds uncompressed and copies .img to repo root
./build-test.sh

# Update a single flake input (e.g. lnbits)
nix flake lock --update-input lnbits
```

The build requires: Nix with flakes enabled, `extra-platforms = aarch64-linux`, QEMU user emulation, and the `nix-community`/`raspberry-pi-nix` Cachix caches. See `docs/development.md` for full setup.

## Running the Web Apps Locally

**Configurator (first-run wizard):**
```bash
cd nixos/configurator-app
python3 -m venv venv && source venv/bin/activate
pip install flask flask-wtf mnemonic
export DEV_MODE=true
python3 app.py
```

**Admin dashboard:**
```bash
cd nixos/admin-app
python3 -m venv venv && source venv/bin/activate
pip install flask flask-wtf
export DEV_MODE=true
python3 app.py
```

`DEV_MODE=true` redirects all file paths to `/tmp/lnbitspi-test/` instead of `/var/lib/`.

**Marketing site (`gh-pages/`):**
```bash
cd gh-pages
npm run dev      # dev server
npm run build    # static site generation (nuxt generate)
npm run preview  # preview built site
```

The `gh-pages/` subdirectory has its own `CLAUDE.md` with design system details.

## Architecture

### System State Machine

The marker file `/var/lib/lnbits/.configured` controls the entire system:

- **Absent** → Caddy routes all traffic to the configurator (port 8080). LNbits and admin services do not start.
- **Present** → Caddy routes traffic to LNbits (port 5000). Admin dashboard (port 8090) is available at `/box/`. Configurator stops.

### Service Map

| Service | Port | NixOS file | Runs when |
|---------|------|------------|-----------|
| Caddy (reverse proxy) | 80/443 | `caddy-proxy.nix` | Always |
| Configurator (wizard) | 8080 | `configurator-service.nix` | Marker absent |
| LNbits | 5000 | `lnbits-service.nix` | Marker present |
| Spark sidecar | 8765 | `spark-sidecar-service.nix` | Marker present |
| Tunnel Me Out reverse tunnel | local 5000 (remote port assigned by provider) | `reverse-tunnel-service.nix` | Tunnel configured + started |
| Admin dashboard | 8090 | `admin-service.nix` | Marker present |
| Tor | — | `tor-service.nix` | Always |
| Wi-Fi config | — | `wifi-config.nix` | First boot |

### Tunnel Me Out Feature

LNbitsBox supports paid reverse tunnels via Tunnel Me Out (lnpro API). The admin app (`nixos/admin-app/app.py`) manages tunnel lifecycle, invoice generation/renewal, and service control.

- Provider API base: `LNBITSBOX_TUNNEL_API_BASE_URL` (default `https://lnbits.lnpro.xyz/reverse_proxy/api/v1`)
- Public product id: `LNBITSBOX_TUNNEL_PUBLIC_ID`
- Tunnel systemd service: `lnbitsbox-reverse-tunnel.service`
- Local forwarded target: `LNBITSBOX_TUNNEL_LOCAL_PORT` (default `5000`)

Admin API endpoints:
- `GET /box/api/tunnel/status` — current tunnel, pending invoice, service status, connect script
- `POST /box/api/tunnel/create-invoice` — create first tunnel invoice
- `POST /box/api/tunnel/renew-invoice` — add days to existing tunnel
- `POST /box/api/tunnel/poll` — check payment status and sync pending invoice state
- `POST /box/api/tunnel/start` — enable + restart reverse tunnel service (requires tunnel + key)
- `POST /box/api/tunnel/stop` — stop reverse tunnel service

UI notes (`nixos/admin-app/templates/dashboard.html`):
- Service row actions are status-driven: `Start` when stopped, `Stop` + `Restart` when active.
- Tunnel service row shows `Create Tunnel` when no tunnel is configured.
- Polling is adaptive (faster when invoice is pending, slower when stable, reduced when tab is hidden).

### Key File Paths (on device)

- `/var/lib/lnbits/.configured` — marker file; creating it triggers switchover
- `/var/lib/lnbits/database.sqlite3` — LNbits database (never deleted by reset)
- `/var/lib/spark-sidecar/mnemonic` — BIP39 seed phrase
- `/var/lib/spark-sidecar/api-key.env` — Spark API key
- `/etc/lnbits/lnbits.env` — LNbits environment config
- `/var/lib/caddy/ca-cert.pem` — self-signed Root CA (persists across reboots)
- `/var/lib/lnbitsbox-update/` — OTA update state (`status`, `log`, `target-version`)
- `/var/lib/lnbitsbox-tunnel/state.json` — tunnel state (`client_id`, `current_tunnel`, `pending_invoice`)
- `/var/lib/lnbitsbox-tunnel/reverse-proxy-key` — private SSH key for tunnel connection
- `/var/lib/lnbitsbox-tunnel/runtime.env` — generated runtime env consumed by reverse tunnel service
- `/etc/lnbitsbox-version` — current version string (written from `flake.nix` `version`)

### Caddy TLS

Caddy uses a self-signed Root CA generated at first boot. The CA persists; the server cert is regenerated each boot to include the current IP in the SAN. HTTP port 80 serves only a cert-trust page and the CA download (`/cert/download`). HTTPS routes: `/box/*` → admin, everything else → LNbits or configurator.

### OTA Update System

On tagged releases, CI:
1. Builds `packages.x86_64-linux.toplevel` (the NixOS system closure)
2. Pushes the closure to `lnbitsbox.cachix.org` via `cachix push`
3. Creates `manifest.json` containing the Nix store path and version
4. Attaches `manifest.json`, the `.img.zst`, and `SHA256SUMS.txt` to the GitHub release

On device, `lnbitsbox-update <tag>`:
1. Downloads `manifest.json` from the release
2. Runs `nix-store --realise <store-path>` (fetches from all configured substituters: `cache.nixos.org` + `lnbitsbox.cachix.org`)
3. Sets the new system profile and activates it with `switch-to-configuration switch`

**Important:** Use `nix-store --realise` (not `nix copy --from <url>`) so that common paths come from `cache.nixos.org` while LNbitsBox-specific paths come from Cachix.

### Versioning

The version string is set in `flake.nix` (`version = "0.x.y"`). Bump it before creating a release tag — it gets written to `/etc/lnbitsbox-version` on the device and embedded in `manifest.json`.

## NixOS Module Layout

```
nixos/
  configuration.nix          # Root imports all modules; users, networking, kernel params
  lnbits-service.nix         # LNbits systemd service + env file
  spark-sidecar-service.nix  # Spark sidecar service
  spark-sidecar-package.nix  # Nix package wrapping spark-sidecar source
  configurator-service.nix   # First-run wizard service
  configurator-package.nix   # Nix package for the configurator Flask app
  admin-service.nix          # Admin dashboard service
  admin-package.nix          # Nix package for the admin Flask app
  caddy-proxy.nix            # TLS cert generation + Caddyfile generation
  tor-service.nix            # Tor hidden service
  wifi-config.nix            # wifi.txt reader on boot
  welcome-screen.nix         # MOTD and login screen
  reset-configurator.nix     # lnbitspi-reset script package
  update-service.nix         # OTA update script + polkit rules
  configurator-app/app.py    # Flask wizard (seed generation, SSH password)
  admin-app/app.py           # Flask admin (system stats, service control, OTA, Wi-Fi)
  cert-trust-page/           # Static HTML page for CA cert installation
```

## LNbits Extension: `reverse_proxy/`

A private LNbits extension for paid SSH tunnel / reverse proxy management. Used with the TunnelMeOut extension. Not part of the NixOS image build — it's installed into LNbits separately.

## CI/CD

GitHub Actions (`.github/workflows/build-image.yml`) triggers on version tags (`v*`) and `workflow_dispatch`. It builds on `ubuntu-latest` using QEMU for aarch64 cross-compilation, pushes the system closure to Cachix, and creates a GitHub release with the image, SHA256SUMS, and manifest.
