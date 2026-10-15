# PrismOS disk installer

> **Status: source complete, never run against a real disk.** The engine, the
> privileged helper and the wizard are covered by unit tests (recorded commands, not
> executed ones) and by the offscreen QML harness. No ISO has been built or booted and
> no partition table has been written by this code. Treat the first run as a
> destructive experiment: use a virtual machine with a throw-away disk image.

The installer puts PrismOS on one **whole disk** of a computer from the live USB. It
is deliberately small: no manual partitioning, no dual boot, no disk encryption.

## What it does

1. **Wizard** (`shell/surfaces/Installer.qml`, opened from the desktop card, the
   launcher entry "Install PrismOS" or `prism-shell ipc installer`): welcome, language /
   keyboard / time zone, network, disk, account, review with typed confirmation,
   progress, done. It is offered only when `/run/archiso` exists (the live USB).
2. **Preview** (`prismctl installer plan`, JSON request on stdin): validates the request
   and returns the partition layout and every command, with the password redacted.
3. **Install** (`prismctl installer install`): re-validates, then asks polkit to run
   `/usr/libexec/prism-installer-helper install`
   (action `org.prismos.installer.install`, `auth_admin`; on the live USB the prompt is expected to take
   the live user's password, `prism`; unverified). The helper re-validates against a fresh `lsblk`, refuses to
   run outside the live USB, and executes the fixed steps below, streaming JSON progress.

## Safety model

| Rule | Where |
| --- | --- |
| Whole disks only; `/dev/NAME` must match a strict pattern and appear in a fresh `lsblk` | `installer.validate` |
| Ineligible: mounted or swapped, read-only, smaller than 16 GB, loop/ram/zram/optical, or the live USB (mounted under `/run/archiso`, ISO 9660, or labelled `PRISM_*` / `ARCHISO*`, so it is caught after *copy to RAM* too) | `installer.classify` |
| The user must type the disk's name; the helper checks it again | `validate(... confirm)` |
| Every command is an argv list; no request text reaches a shell | `installer.steps` |
| Hostname, user name, full name, password, locale, keyboard and time zone are matched against patterns or allowlists | `installer.validate`, `regional.py` |
| The password travels on stdin only (QML → `prismctl` → `pkexec` → helper → `chpasswd`) and is never in argv, a preview or a log | tests assert this |
| Writes into the new system are contained (`realpath` check, `O_NOFOLLOW`) | `Host.write` |
| The helper is root-only, takes exactly the argument `install`, and runs with `python3 -I` | `bin/prism-installer-helper` |
| On failure the target is unmounted; a stale target mount from a failed attempt does not block a retry | `execute`, `classify` |

## Disk layout and steps

GPT in both modes. UEFI: 1 GiB FAT32 EFI system partition mounted at `/boot` (kernel,
initramfs and GRUB live there), then ext4 `prismos` for the rest. BIOS: 1 MiB BIOS boot
partition, then ext4. Swap is zram (`zram-generator`), not a partition.

`wipefs` → `sgdisk` → wait for partition nodes → `mkfs.ext4` (and `mkfs.fat`) → mount →
`pacstrap` (base, linux, linux-firmware, CPU microcode, grub, efibootmgr on UEFI,
NetworkManager, sudo, `prism-shell` and the desktop stack it depends on, greetd and
tuigreet, mesa/Vulkan drivers, Firefox, fonts) → `genfstab -U` → hostname, hosts, locale,
console keymap, time zone, sudoers (`wheel`), greetd (tuigreet, **no autologin**), zram,
saved Wi-Fi profiles (mode 0600) → `useradd`, `chpasswd`, root locked, the user's
PrismOS config and chosen keyboard layout → `systemctl enable` NetworkManager, bluetooth,
greetd, timesyncd → GRUB (UEFI: a `PrismOS` NVRAM entry, best effort, plus the removable
fallback path; BIOS: `i386-pc`) and `grub-mkconfig` → `sync`, `umount -R`.

`BASE_PACKAGES`, `SERVICES` and the layout are constants in `prismos/installer.py`.

## Requirements and limits

- **Network is required.** The base system comes from the Arch mirrors configured on the
  live USB. Only `prism-shell` comes from the repository bundled at
  `/opt/prismos/repo` on the ISO (`scripts/build-iso.sh`, unsigned: `SigLevel = Optional
  TrustAll`, same trust as the ISO itself). A fully offline install is not supported.
- The installed system has **no `[prismos]` repository**, so `prism-shell` updates need a
  published repo (roadmap M3 item 6).
- No encryption, LVM, RAID, Btrfs, manual partitioning, dual boot, Secure Boot, hibernation
  or custom mirror selection. Other operating systems on the chosen disk are erased.
- The GRUB menu says "Arch Linux"; it has not been branded.
- The first login runs the ordinary PrismOS first-run wizard.

## Trying it safely

```bash
# 1. Build the ISO on Arch (see README), then make a throw-away disk
qemu-img create -f qcow2 /tmp/prism-target.qcow2 40G
# 2. UEFI VM
qemu-system-x86_64 -enable-kvm -m 4G -smp 2 -cpu host \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.4m.fd \
  -drive file=/tmp/prism-target.qcow2,if=virtio -cdrom out/prismos-*.iso -boot d \
  -nic user
# 3. In the live session choose "Install PrismOS"; reboot without the ISO.
```

Repeat with SeaBIOS (omit the `pflash` line) for the BIOS path and on an NVMe-backed disk
(`-device nvme`) for partition naming. From a terminal you can preview a plan without
changing anything: `printf '%s' "$JSON" | prismctl installer plan`.

## Acceptance still to do

UEFI and BIOS boots of the installed system, NVMe/virtio/SATA naming, failure and retry
(unplugged network, full disk), a laptop on battery, localized installs, the polkit prompt
on the live session, `grub-install` and `efibootmgr` in a chroot on real firmware, and a
login to the installed desktop. Record results in `docs/VALIDATION.md`.
