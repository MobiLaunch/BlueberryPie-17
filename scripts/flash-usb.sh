#!/usr/bin/env bash
# Safely write a previously generated PrismOS live ISO to a removable USB disk.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: sudo bash ./scripts/flash-usb.sh /dev/sdX [out/PrismOS.iso]"
    echo "WARNING: Every partition on the target USB disk will be erased."
    exit 2
fi
(( EUID == 0 )) || { echo "Run this script with sudo." >&2; exit 1; }
for cmd in lsblk blockdev dd sync readlink; do
    command -v "$cmd" >/dev/null || { echo "Missing command: $cmd" >&2; exit 1; }
done
target="$(readlink -f -- "$1")"
[[ -b "$target" ]] || { echo "Target is not a block device: $1" >&2; exit 1; }
[[ "$(lsblk -dnro TYPE -- "$target")" == "disk" ]] || {
    echo "Select the entire disk (e.g. /dev/sdb), NOT /dev/sdb1." >&2; exit 1;
}
[[ "$(lsblk -dnro TRAN -- "$target")" == "usb" ]] || {
    echo "Refusing to erase a disk that is not explicitly identified as USB." >&2; exit 1;
}
mounts="$(lsblk -nr -o MOUNTPOINTS -- "$target")"
[[ -z "${mounts//[[:space:]]/}" ]] || {
    echo "USB partitions are mounted; unmount them using 'udisksctl unmount -b /dev/sdX1' or 'sudo umount ...' first." >&2
    exit 1
}
if (( $# == 2 )); then
    iso="$(readlink -f -- "$2")"
else
    shopt -s nullglob
    images=( "$root"/out/*.iso )
    (( ${#images[@]} == 1 )) || {
        echo "Expected exactly one .iso in out/. Specify ISO explicitly if multiple exist." >&2; exit 1;
    }
    iso="${images[0]}"
fi
[[ -f "$iso" && -s "$iso" ]] || { echo "ISO not found or empty: $iso" >&2; exit 1; }
printf '\nISO file: %s\nUSB target: %s\n' "$iso" "$target"
lsblk -d -o NAME,SIZE,MODEL,TRAN -- "$target"
echo "DANGER: This permanently overwrites the USB disk and ALL its partitions."
read -r -p "To proceed, type exactly ERASE $target : " confirmation
[[ "$confirmation" == "ERASE $target" ]] || { echo "Cancelled without writing."; exit 1; }
[[ "$(lsblk -dnro TRAN -- "$target")" == "usb" ]] || {
    echo "Device identification changed; refusing to write." >&2; exit 1;
}
dd if="$iso" of="$target" bs=4M status=progress conv=fsync
sync
echo "USB written. You can now reboot and choose the USB in the boot menu."
