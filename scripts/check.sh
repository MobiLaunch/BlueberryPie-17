#!/usr/bin/env bash
set -euo pipefail
prism_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$prism_root"
python3 -m unittest discover -s tests -v
while IFS= read -r prism_script; do bash -n "$prism_script"; done < <(find scripts bin archiso -type f \( -name '*.sh' -o -name prism-shell -o -name prism-session \))
bash -n packaging/arch/PKGBUILD
node --check preview/app.js
python3 -m compileall -q prismos scripts/generate-design.py
if command -v qmlformat >/dev/null; then
    while IFS= read -r prism_qml; do qmlformat "$prism_qml" >/dev/null; done < <(find shell -name '*.qml')
    echo 'QML syntax check passed.'
else
    echo 'QML parse skipped: install qt6-declarative for qmlformat.'
fi
echo 'PrismOS source checks passed. Native compositor and ISO boot checks are separate.'
