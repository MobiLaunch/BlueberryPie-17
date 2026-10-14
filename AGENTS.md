# PrismOS development conventions

- Work in the new project; do not import unrelated distro configuration.
- Native shell UI uses shared components and semantic theme roles.
- System reads/writes belong in `prismos`; never interpolate shell commands.
- Treat Android 17 fidelity as a measured acceptance target. Do not call a
  preview or a launch splash a complete OS or actual compositor surface morph.
- Keep existing personal configs untouched; PrismOS owns a separate session.
- Preserve the complete upstream archiso releng profile and boot parameter relationships.
- Run adapter tests and relevant preview/QML checks after functional changes.
- Record unexecuted hardware/ISO checks clearly in `docs/VALIDATION.md`.
