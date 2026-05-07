# Phoenixd Upgrade Guide

This project packages Phoenixd from source as a JVM application instead of using ACINQ's prebuilt `linux-arm64` binary.

That choice is intentional: on NixOS Raspberry Pi builds, the ACINQ ARM64 binary has issues LSP connectivity. Building Phoenixd from source with the JVM distribution fixed that issue.

Use this guide whenever you want to upgrade Phoenixd, for example from `0.7.3` to `0.7.4`.

## Overview

A Phoenixd upgrade usually touches these files:

- `flake.nix`
- `flake.lock`
- `nixos/phoenixd-package.nix`
- `nixos/phoenixd-no-git.patch`
- `nixos/phoenixd-deps.json`

In practice, the work is:

1. Update the Phoenixd source input.
2. Update the packaged Phoenixd version.
3. Check whether the upstream Gradle wrapper version changed.
4. Regenerate the Gradle dependency lock file on the Debian build machine.
5. Build the Phoenixd package.
6. Build the full image.

## 1. Update the Phoenixd source input

Edit `flake.nix` and change the Phoenixd input tag:

```nix
phoenixd.url = "github:ACINQ/phoenixd/v0.7.4";
```

Then update the flake lock:

```bash
nix flake lock --update-input phoenixd
```

This updates `flake.lock` to the new Phoenixd source revision and hash.

## 2. Update the packaged Phoenixd version

In `nixos/phoenixd-package.nix`, update:

```nix
version = "0.7.4";
```

This version string is used when installing the generated `jvmDistZip` artifact.

## 3. Check the upstream Gradle wrapper version

Phoenixd is built with a pinned Gradle version in `nixos/phoenixd-package.nix` to match upstream and avoid Gradle/Kotlin DSL mismatches.

Check the upstream wrapper version:

```bash
grep distributionUrl gradle/wrapper/gradle-wrapper.properties
```

If upstream changed the wrapper version, update the custom Gradle version in `nixos/phoenixd-package.nix`.

Example:

```nix
version = "8.9";
hash = "sha256-...";
```

To compute the Nix-style hash for a Gradle distribution:

1. Take the upstream `distributionSha256Sum` value from `gradle-wrapper.properties`.
2. Convert it from hex to Nix `sha256-...` base64 format.

One way to do that:

```bash
python3 - <<'PY'
import base64, binascii
hexhash = "PUT_UPSTREAM_HEX_SHA256_HERE"
print("sha256-" + base64.b64encode(binascii.unhexlify(hexhash)).decode())
PY
```

If the wrapper version did not change, leave the Gradle pin alone.

## 4. Check whether the local patch still applies

This repo patches Phoenixd so that:

- it does not require a live `.git` checkout during the Nix build
- it can skip native targets and build JVM-only
- Gradle plugin resolution includes `mavenCentral()`

The patch lives in:

- `nixos/phoenixd-no-git.patch`

After bumping Phoenixd, build output will tell you if this patch no longer applies cleanly.

If it fails during `patchPhase`, refresh the patch against the new upstream sources before continuing.

## 5. Regenerate the Gradle dependency lock on the Debian builder

Do this on the Debian/Ubuntu machine you use for real builds, not on macOS.

Generate the dependency update script:

```bash
nix-build -E 'let pkgs = import <nixpkgs> {}; phoenixd = pkgs.fetchFromGitHub { owner = "ACINQ"; repo = "phoenixd"; rev = "REV_FROM_FLAKE_LOCK"; hash = "NAR_HASH_FROM_FLAKE_LOCK"; }; in (pkgs.callPackage ./nixos/phoenixd-package.nix { inherit phoenixd; }).mitmCache.updateScript'
```

That command prints a `/nix/store/...-fetch-deps.sh` path.

Run the printed script:

```bash
/nix/store/...-fetch-deps.sh
```

This regenerates:

- `nixos/phoenixd-deps.json`

Important:

- Regenerate `phoenixd-deps.json` whenever the Phoenixd source changes.
- Regenerate it whenever the Gradle version changes.
- If package build errors mention missing Maven or Kotlin artifacts, the lock file may be stale.

## 6. Build the Phoenixd package

First test the package by itself:

```bash
nix build .#packages.x86_64-linux.phoenixd -L
```

If you build natively on Linux ARM, you can also test:

```bash
nix build .#packages.aarch64-linux.phoenixd -L
```

This should produce a working JVM-based Phoenixd package containing:

- `bin/phoenixd`
- `bin/phoenix-cli`

## 7. Build the full LNbitsBox image

Once the Phoenixd package build succeeds, build the full image:

```bash
nix build .#sdImageUncompressed -L
```

Or the release image:

```bash
nix build .#sdImage -L
```

## 8. Validate on Raspberry Pi

After flashing or deploying the image, validate on the Pi:

```bash
phoenix-cli getinfo
phoenix-cli createinvoice --amountSat=1000 --desc="upgrade test"
```

Then pay that invoice from another Lightning wallet or node.

The key regression to watch for is:

- Phoenixd starts and connects
- invoice creation works
- but invoices are not payable

If that regression returns, do not switch back to the upstream prebuilt ARM64 binary. Keep investigating the source-built JVM path.

## Troubleshooting

### Patch fails during `patchPhase`

The upstream Phoenixd sources changed enough that `nixos/phoenixd-no-git.patch` needs to be refreshed.

### `kotlin-stdlib` or `kotlin-reflect` artifact not found

Usually one of these is true:

- the Gradle pin in `nixos/phoenixd-package.nix` does not match upstream closely enough
- `nixos/phoenixd-deps.json` is stale
- the patch adding `mavenCentral()` is missing or no longer applies

### `attribute 'mkGradle' missing`

Your local `nixpkgs` revision exposes Gradle internals differently. The package file in this repo is written to support both the newer and older nixpkgs layouts. Make sure you are using the current repo version of `nixos/phoenixd-package.nix`.

## Suggested upgrade checklist

```text
[ ] Update `flake.nix` Phoenixd tag
[ ] Run `nix flake lock --update-input phoenixd`
[ ] Update `version` in `nixos/phoenixd-package.nix`
[ ] Check `gradle-wrapper.properties` upstream
[ ] Update Gradle pin if wrapper version changed
[ ] Refresh `nixos/phoenixd-no-git.patch` if needed
[ ] Regenerate `nixos/phoenixd-deps.json` on Debian
[ ] Build `.#packages.x86_64-linux.phoenixd`
[ ] Build `.#sdImageUncompressed`
[ ] Test invoice creation and payment on Pi
```
