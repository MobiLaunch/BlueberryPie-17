#!/usr/bin/env bash
set -euo pipefail
prism_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
prism_package=""
prism_releng=/usr/share/archiso/configs/releng
prism_stage_only=false
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --package) prism_package="${2:?Missing package path}"; shift 2;;
        --releng) prism_releng="${2:?Missing releng path}"; shift 2;;
        --stage-only) prism_stage_only=true; shift;;
        *) echo 'Usage: build-iso.sh --package /path/to/prism-shell.pkg.tar.zst [--stage-only] [--releng /path/to/releng]' >&2; exit 2;;
    esac
done
[[ -f "$prism_package" ]] || { echo 'Build a prism-shell package first and pass --package.' >&2; exit 1; }
[[ -f "$prism_releng/profiledef.sh" ]] || { echo 'Install archiso; the complete releng profile is required.' >&2; exit 1; }
for prism_tool in repo-add bsdtar python3 rg; do
    command -v "$prism_tool" >/dev/null || { echo "Missing $prism_tool" >&2; exit 1; }
done
if ! bsdtar -xOf "$prism_package" .PKGINFO | rg -q '^pkgname = prism-shell$'; then
    echo 'The supplied package is not prism-shell.' >&2; exit 1
fi
if [[ "$prism_stage_only" == false && "$EUID" -ne 0 ]]; then
    echo 'A complete ISO build needs root: sudo scripts/build-iso.sh --package …' >&2; exit 1
fi
prism_profile="$prism_root/build/archiso-profile"
mkdir -p -- "$prism_root/build"
prism_staging="$(mktemp -d "$prism_root/build/.archiso-stage-XXXXXX")"
trap 'rm -rf -- "$prism_staging"' EXIT
cp -a -- "$prism_releng/." "$prism_staging/"
python3 - "$prism_staging" "$prism_root" <<'PY'
import pathlib, sys
profile, root = map(pathlib.Path, sys.argv[1:])
path = profile/'profiledef.sh'
text = path.read_text()
# Append shell assignments, preserving releng boot modes, permissions,
# architecture and install_dir. Keep archisobasedir/INSTALL_DIR consistent.
text += '\niso_name="prismos"\niso_label="PRISM_$(date +%Y%m)"\niso_publisher="MobiLaunch"\niso_application="PrismOS Live Desktop"\n'
text += '\nfile_permissions["/usr/local/sbin/prismos-live-user"]="0:0:755"\n'
path.write_text(text)
packages = (profile/'packages.x86_64').read_text().splitlines()
packages += (root/'archiso/packages.x86_64').read_text().splitlines()
(profile/'packages.x86_64').write_text('\n'.join(dict.fromkeys(packages))+'\n')
PY
prism_airoot="$prism_staging/airootfs"
install -Dm755 "$prism_root/archiso/live-user.sh" "$prism_airoot/usr/local/sbin/prismos-live-user"
install -Dm644 "$prism_root/archiso/prismos-live-user.service" "$prism_airoot/etc/systemd/system/prismos-live-user.service"
install -Dm644 "$prism_root/archiso/greetd.toml" "$prism_airoot/etc/greetd/config.toml"
mkdir -p -- "$prism_airoot/etc/systemd/system/multi-user.target.wants" "$prism_airoot/etc/systemd/system/greetd.service.d" "$prism_staging/repo"
ln -sfn /etc/systemd/system/prismos-live-user.service "$prism_airoot/etc/systemd/system/multi-user.target.wants/prismos-live-user.service"
ln -sfn /usr/lib/systemd/system/NetworkManager.service "$prism_airoot/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
ln -sfn /usr/lib/systemd/system/bluetooth.service "$prism_airoot/etc/systemd/system/multi-user.target.wants/bluetooth.service"
ln -sfn /usr/lib/systemd/system/greetd.service "$prism_airoot/etc/systemd/system/multi-user.target.wants/greetd.service"
cat > "$prism_airoot/etc/systemd/system/greetd.service.d/prismos.conf" <<'UNIT'
[Unit]
Requires=prismos-live-user.service
After=prismos-live-user.service
Conflicts=getty@tty1.service
UNIT
rm -f -- "$prism_airoot/etc/systemd/system/getty@tty1.service.d/autologin.conf"
cat > "$prism_airoot/etc/os-release" <<'OS'
NAME="PrismOS"
PRETTY_NAME="PrismOS 0.7 Live Preview"
ID=prismos
ID_LIKE=arch
VERSION_ID=0.7
OS
install -d -m755 "$prism_airoot/etc/sudoers.d"
printf '%%wheel ALL=(ALL:ALL) NOPASSWD: ALL\n' > "$prism_airoot/etc/sudoers.d/prismos-live"
chmod 440 "$prism_airoot/etc/sudoers.d/prismos-live"
cp -- "$prism_package" "$prism_staging/repo/"
repo-add "$prism_staging/repo/prismos.db.tar.gz" "$prism_staging/repo/$(basename -- "$prism_package")"
# Commit the stage at its fixed final location before writing the local repo URL.
rm -rf -- "$prism_profile"
mv -- "$prism_staging" "$prism_profile"
cat >> "$prism_profile/pacman.conf" <<REPO

[prismos]
SigLevel = Optional TrustAll
Server = file://$prism_profile/repo
REPO
echo "Prepared complete releng profile at $prism_profile"
if [[ "$prism_stage_only" == true ]]; then exit 0; fi
command -v mkarchiso >/dev/null || { echo 'Install archiso for mkarchiso.' >&2; exit 1; }
# A changed staged rootfs requires a clean archiso workdir.
if [[ -d "$prism_root/build/archiso-work" ]]; then
    echo 'An archiso workdir already exists. Move or remove build/archiso-work before a fresh build.' >&2
    exit 1
fi
mkarchiso -v -w "$prism_root/build/archiso-work" -o "$prism_root/out" "$prism_profile"
