# Build a PrismOS ISO from Windows 10/11

PrismOS is an Arch Linux **live ISO**. Windows PowerShell, CMD and ordinary
Windows Git Bash cannot run `mkarchiso` natively. There are two supported
workflows below. Do not execute `bash build.sh` in PowerShell.

## Option 1 — Click Build ISO on GitHub (easiest)

This starts an Arch Linux container on a GitHub-hosted Linux runner. Your
Windows computer just downloads the finished ISO.

1. Open [BlueberryPie-17 → Actions](https://github.com/MobiLaunch/BlueberryPie-17/actions).
2. Select **Build PrismOS ISO** in the left sidebar.
3. Click **Run workflow**, select `main`, and click the green **Run workflow**.
4. Open the newly created workflow run. A **green check** means all steps
   succeeded. A red X means do **not** treat its files as a completed ISO.
5. At the bottom under **Artifacts**, download `PrismOS-v0.8-ISO`.
6. Windows will receive a ZIP file. Extract it to obtain the `.iso` and
   `SHA256SUMS`. Do not try to flash the artifact ZIP as an ISO.

The workflow needs an online connection, enough GitHub Actions minutes and
repository permissions. It uses an Arch container with privileged kernel
mounts because ArchISO builds require filesystem/loop operations. The GitHub
runner may deny these capabilities; if it does, use the local VM route below.
A successful workflow proves an ISO file was produced, **not** that it boots
or runs on every PC.

## Option 2 — Build locally in VirtualBox (most reliable)

Install [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads) and
download the current official [Arch Linux ISO](https://archlinux.org/download/).

1. In VirtualBox create an Arch Linux **64-bit** VM with approximately
   **8 GB RAM, 4 CPUs and an 80 GB dynamically allocated disk**. The VM needs
   internet connectivity. Attach the official Arch ISO in its optical drive.
2. Boot the VM. At the live Arch terminal run `archinstall`. Choose a
   normal guided install using the VM's *virtual disk*, NetworkManager, a
   regular user and an appropriate bootloader. **Never select your Windows
   physical disk.** Restart into the installed Arch VM and log in as the
   regular user (not root).
3. Install the tools and clone the project in the **VM's Linux filesystem**:

   ```bash
   sudo pacman -Syu --needed base-devel archiso git ripgrep pacman-contrib python-pillow sudo
   git clone https://github.com/MobiLaunch/BlueberryPie-17.git
   cd BlueberryPie-17
   bash ./build.sh
   ```

4. When complete, check the ISO file:

   ```bash
   ls -lh out/*.iso
   ```

   The file is in `~/BlueberryPie-17/out/`, **inside the Arch VM**. If
   something fails, inspect `build/iso-build.log`; also check the terminal
   output if it failed before the log could be created.

### Get the ISO from the Arch VM onto Windows

One method is a temporary VirtualBox NAT port-forward, which avoids shared
folder drivers:

1. Shut down the VM. VirtualBox **Settings → Network → Adapter 1 → Advanced →
   Port Forwarding**: add TCP rule, Host IP `127.0.0.1`, Host Port `8000`,
   Guest Port `8000`, and leave Guest IP blank. Start the VM.
2. In the Arch VM run:

   ```bash
   cd ~/BlueberryPie-17/out
   python -m http.server 8000 --bind 0.0.0.0
   ```

3. On Windows open `http://127.0.0.1:8000/` and click the `.iso` file
   to download it. Stop the temporary HTTP server with Ctrl+C.

This serves the ISO only while the Python command is running, with the host
port forwarded to Windows localhost. If it does not connect, verify the NAT
adapter and forwarding rule.

### Common errors

| Error | Fix |
| --- | --- |
| `bash` not recognized in Windows | Build inside the Arch VM (or click GitHub Actions). |
| `No such file or directory` for `build.sh` | Run `pwd`, `ls -la`, and `cd ~/BlueberryPie-17` **in the VM**. |
| `Missing repo-add` | `sudo pacman -S pacman-contrib` |
| `Missing rg` | `sudo pacman -S ripgrep` |
| `Missing mkarchiso` | `sudo pacman -S archiso` |
| `makepkg cannot run as root` | Log in as a normal Arch user; do not run `sudo bash build.sh`. |
| Build succeeds but reboot does not start PrismOS | The ISO is still experimental; boot/installer qualification is outstanding. |
| Building directly under `/mnt/c/` in WSL | Use a Linux-native filesystem; NTFS does not reliably preserve ArchISO permissions/symlinks. |

For the latest build run and its logs, see the
[Actions page](https://github.com/MobiLaunch/BlueberryPie-17/actions).
