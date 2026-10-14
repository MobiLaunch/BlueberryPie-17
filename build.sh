#!/usr/bin/env bash
# Build PrismOS package and Arch live ISO, from any current working directory.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$root"
if (( EUID == 0 )); then echo "Run as your normal user: bash ./build.sh" >&2; exit 1; fi
stage_only=false
case "${1:-}" in
    "") ;;
    --stage-only) stage_only=true ;;
    -h|--help) echo "Usage: bash ./build.sh [--stage-only]"; exit 0 ;;
    *) echo "Usage: bash ./build.sh [--stage-only]" >&2; exit 2 ;;
esac
for utility in makepkg sudo mkarchiso repo-add bsdtar rg python3; do
    if ! command -v "$utility" >/dev/null; then
        echo "Missing $utility. On Arch: sudo pacman -Syu --needed base-devel archiso git ripgrep pacman-contrib python-pillow sudo" >&2
        exit 1
    fi
done
[[ -f /usr/share/archiso/configs/releng/profiledef.sh ]] || { echo "Missing Arch releng profile; install archiso." >&2; exit 1; }
echo "[1/3] Packaging PrismOS as your regular user..."
bash "$root/scripts/build-package.sh"
shopt -s nullglob
packages=( "$root"/build/package/prism-shell-*.pkg.tar.zst )
(( ${#packages[@]} > 0 )) || { echo "No built prism-shell package found under build/package." >&2; exit 1; }
package="${packages[0]}"
for candidate in "${packages[@]}"; do
    [[ "$candidate" -nt "$package" ]] && package="$candidate"
done
printf '[2/3] Package: %s\n' "$package"
mkdir -p "$root/build"
echo "[3/3] Preparing Arch releng profile and live ISO..."
args=( --package "$package" )
$stage_only && args+=( --stage-only )
sudo bash "$root/scripts/build-iso.sh" "${args[@]}" 2>&1 | tee "$root/build/iso-build.log"
if $stage_only; then
    echo "Profile staged at build/archiso-profile (no ISO built)."
else
    echo "ISO files in $root/out:"
    find "$root/out" -maxdepth 1 -type f -name '*.iso' -print
fi
echo "Log saved to build/iso-build.log"
