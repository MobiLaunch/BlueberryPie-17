#!/usr/bin/env bash
set -euo pipefail
prism_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo 'This command needs an existing Wayland session. Use the installed PrismOS login session from a TTY instead.' >&2
    exit 1
fi
exec "$prism_root/bin/prism-shell" "$@"
