#!/usr/bin/env bash
set -euo pipefail
# Runs only inside the live rootfs. There is no disk installer in v0.1.
if ! id prism >/dev/null 2>&1; then
    useradd --create-home --groups wheel,audio,video,input --shell /bin/bash prism
    printf 'prism:prism\n' | chpasswd
fi
install -d -m 700 -o prism -g prism /home/prism/.config/prismos/hypr
for prism_config_name in hyprland.lua hyprlock.conf; do
    if [[ ! -e "/home/prism/.config/prismos/hypr/$prism_config_name" ]]; then
        cp -- "/usr/share/prismos/config/hypr/$prism_config_name" /home/prism/.config/prismos/hypr/
    fi
done
chown -R prism:prism /home/prism/.config
