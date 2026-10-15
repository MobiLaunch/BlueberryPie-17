#!/usr/bin/env bash
set -euo pipefail
prism_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$EUID" -eq 0 ]]; then
    echo 'Build packages as your regular user, not root.' >&2; exit 1
fi
for prism_tool in makepkg tar sha256sum python3; do
    command -v "$prism_tool" >/dev/null || { echo "Missing $prism_tool" >&2; exit 1; }
done
python3 "$prism_root/scripts/generate-design.py"
prism_build="$prism_root/build/package"
mkdir -p -- "$prism_build/PrismOS-0.9.0"
for prism_path in bin prismos shell design config docs packaging LICENSE; do
    cp -r -- "$prism_root/$prism_path" "$prism_build/PrismOS-0.9.0/"
done
find "$prism_build/PrismOS-0.9.0" -type d -name __pycache__ -prune -exec rm -rf -- {} +
tar -czf "$prism_build/PrismOS-0.9.0.tar.gz" -C "$prism_build" PrismOS-0.9.0
prism_hash="$(sha256sum "$prism_build/PrismOS-0.9.0.tar.gz")"
prism_hash="${prism_hash%% *}"
sed "s/GENERATED_BY_BUILD_SCRIPT/$prism_hash/" "$prism_root/packaging/arch/PKGBUILD" > "$prism_build/PKGBUILD"
cd -- "$prism_build"
makepkg -s --noconfirm --cleanbuild "$@"
