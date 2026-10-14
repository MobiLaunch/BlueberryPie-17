#!/usr/bin/env bash
set -euo pipefail
prism_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
prism_repo="${1:-MobiLaunch/BlueberryPie-17}"
if [[ ! "$prism_repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
    echo 'Use owner/repository format' >&2; exit 2
fi
command -v gh >/dev/null || { echo 'Install GitHub CLI first: sudo pacman -S github-cli' >&2; exit 1; }
cd -- "$prism_root"
gh auth status
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo 'Use a committed clone of the repository to publish updates.' >&2; exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
    echo 'Commit or stash local changes before publishing.' >&2; exit 1
fi
gh repo view "$prism_repo" >/dev/null
prism_origin="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "$prism_origin" ]]; then
    git remote add origin "https://github.com/$prism_repo.git"
elif [[ "$prism_origin" != "https://github.com/$prism_repo.git" && "$prism_origin" != "git@github.com:$prism_repo.git" ]]; then
    echo 'origin points to another repository. Resolve it before publishing.' >&2; exit 1
fi
gh auth setup-git
git fetch origin main
if ! git merge-base --is-ancestor origin/main HEAD; then
    echo 'Your branch must contain remote main. Merge or rebase the current remote history first.' >&2; exit 1
fi
git push -u origin HEAD:main
