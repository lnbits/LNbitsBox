{ pkgs, ... }:

let
  mountRoot = "/run/media/lnbitsbox";

  usbMountScript = pkgs.writeShellScript "lnbitsbox-usb-mount" ''
    set -eu

    device="$1"
    mount_root="${mountRoot}"

    sanitize() {
      printf '%s' "$1" | tr -cs 'A-Za-z0-9._-' '_' | sed 's/^_\+//; s/_\+$//'
    }

    [ -b "$device" ] || exit 0

    existing_target="$(findmnt -rn -S "$device" -o TARGET 2>/dev/null || true)"
    if [ -n "$existing_target" ]; then
      echo "USB backup drive already mounted at $existing_target"
      exit 0
    fi

    fstype=""
    label=""
    uuid=""
    for _ in $(seq 1 10); do
      fstype="$(blkid -o value -s TYPE "$device" 2>/dev/null || true)"
      label="$(blkid -o value -s LABEL "$device" 2>/dev/null || true)"
      uuid="$(blkid -o value -s UUID "$device" 2>/dev/null || true)"
      if [ -n "$fstype" ]; then
        break
      fi
      sleep 1
    done

    if [ -z "$fstype" ]; then
      echo "USB backup drive $device is present but filesystem type is not ready yet"
      exit 1
    fi

    case "$fstype" in
      vfat|msdos)
        mount_opts="rw,nosuid,nodev,noexec,uid=0,gid=0,umask=0077"
        ;;
      exfat|ext2|ext3|ext4|btrfs|xfs|ntfs|ntfs3)
        mount_opts="rw,nosuid,nodev,noexec"
        ;;
      *)
        echo "Skipping unsupported USB filesystem type: $fstype"
        exit 0
        ;;
    esac

    base_name="$(basename "$device")"
    dir_name="$(sanitize "''${label:-''${uuid:-$base_name}}")"
    [ -n "$dir_name" ] || dir_name="$base_name"

    target="$mount_root/$dir_name"
    mkdir -p "$target"

    for _ in $(seq 1 5); do
      if mount -t "$fstype" -o "$mount_opts" "$device" "$target"; then
        echo "Mounted USB backup drive $device at $target"
        exit 0
      fi
      sleep 1
    done

    echo "Failed to mount USB backup drive $device at $target"
    if ! findmnt -rn "$target" >/dev/null 2>&1; then
      rmdir "$target" 2>/dev/null || true
    fi
    exit 1
  '';

  usbCleanupScript = pkgs.writeShellScript "lnbitsbox-usb-cleanup" ''
    set -eu

    mount_root="${mountRoot}"
    findmnt -rn -o SOURCE,TARGET | while read -r source target; do
      case "$target" in
        "$mount_root"/*)
          if [ ! -b "$source" ]; then
            umount -l "$target" 2>/dev/null || true
            rmdir "$target" 2>/dev/null || true
          fi
          ;;
      esac
    done
  '';
in
{
  boot.supportedFilesystems = [ "exfat" "ntfs" ];

  systemd.tmpfiles.rules = [
    "d ${mountRoot} 0755 root root - -"
  ];

  systemd.services."lnbitsbox-usb-mount@" = {
    description = "Auto-mount USB backup drive %I";
    after = [ "local-fs.target" ];
    serviceConfig = {
      Type = "oneshot";
    };
    path = with pkgs; [ coreutils gnused util-linux ];
    script = ''
      ${usbMountScript} "/dev/%I"
    '';
  };

  systemd.services.lnbitsbox-usb-cleanup = {
    description = "Clean up stale LNbitsBox USB mounts";
    serviceConfig = {
      Type = "oneshot";
    };
    path = with pkgs; [ coreutils util-linux ];
    script = ''
      ${usbCleanupScript}
    '';
  };

  systemd.services.lnbitsbox-usb-scan = {
    description = "Mount existing USB backup drives at boot";
    wantedBy = [ "multi-user.target" ];
    after = [ "local-fs.target" "systemd-udevd.service" ];
    serviceConfig = {
      Type = "oneshot";
    };
    path = with pkgs; [ coreutils gawk systemd util-linux ];
    script = ''
      for symlink in /dev/disk/by-id/usb-*-part*; do
        [ -e "$symlink" ] || continue
        device="$(readlink -f "$symlink")"
        ${usbMountScript} "$device" || true
      done
      ${usbCleanupScript}
    '';
  };

  services.udev.extraRules = ''
    ACTION=="add", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", ENV{ID_BUS}=="usb", TAG+="systemd", ENV{SYSTEMD_WANTS}+="lnbitsbox-usb-mount@%k.service"
    ACTION=="remove", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", ENV{ID_BUS}=="usb", TAG+="systemd", ENV{SYSTEMD_WANTS}+="lnbitsbox-usb-cleanup.service"
  '';
}
