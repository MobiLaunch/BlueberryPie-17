#!/usr/bin/env bash
set -euo pipefail
prism_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
echo 'Preview: http://127.0.0.1:8787/ (Ctrl+C to stop)'
exec python3 -m http.server 8787 --bind 127.0.0.1 --directory "$prism_root/preview"
