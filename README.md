<p align="center"><img src="tfa/brand/logo-light.svg" alt="Thinking Fish Assist" width="420"></p>

# Thinking Fish Assist

Remote support software used by [Thinking Fish Ltd](https://thinking.fish) to help its customers.
Customers download it from **https://thinking.fish/assist**.

Thinking Fish Assist is a modified build of **[RustDesk](https://github.com/rustdesk/rustdesk)**
(version 1.4.9), which is free software under the **GNU Affero General Public License v3**
([LICENCE](LICENCE)). This repository is the complete corresponding source of every
Thinking Fish Assist build we distribute, as the AGPL requires. RustDesk is © Purslane Tech Pte. Ltd.
and its contributors; all upstream history and copyright notices are kept. "RustDesk" is a
trademark of its owners; this product is not affiliated with or endorsed by them, and their name
and logo have been removed from the user interface (they remain only in attribution and in code).

## What is different from upstream RustDesk

| Change | Where |
|---|---|
| Name, icons, colours (Thinking Fish orange), window titles, tray, About page, installer text | `src/branding.rs`, `tfa/brand/`, `flutter/lib/consts.dart`, platform metadata |
| Our ID/relay server `assist.thinkingfish.com`, its public key and the API server are baked in and locked | `src/branding.rs` (overridable at build time: `TFA_RENDEZVOUS_SERVER`, `TFA_RS_PUB_KEY`, `TFA_API_SERVER`) |
| Never offers RustDesk's own updates | `src/branding.rs` |
| Links go to thinking.fish; About shows the source-code link | Flutter UI |
| CI builds only Windows x64, macOS (Apple silicon + Intel) and Android | `.github/workflows/tfa-build.yml`, `tfa-release.yml` |

The internal app name is `ThinkingFishAssist` (no spaces) because upstream uses it for the install
folder, Windows service, launchd labels, config directory and URI scheme; people see
"Thinking Fish Assist".

## Server

The client talks to a self-hosted open-source RustDesk server (`hbbs`/`hbbr` 1.1.16) and the
MIT-licensed [rustdesk-api](https://github.com/lejianwen/rustdesk-api) for staff logins, the shared
address book and the device list. No RustDesk Server Pro licence is involved.

## Building a release

Push a tag `vX.Y.Z` (or run **Actions > Thinking Fish Assist release** by hand with a test tag).
The workflow builds everything and attaches it to a GitHub release:

| File | What |
|---|---|
| `ThinkingFishAssist-windows-x64.exe` | Run-or-install (runs without installing; has an Install button) |
| `ThinkingFishAssist-windows-x64.msi` | For managed/silent installs (`msiexec /i ... /qn`) |
| `ThinkingFishAssist-macos-aarch64.dmg` / `-x86_64.dmg` | Apple silicon / Intel Macs |
| `ThinkingFishAssist-android.apk` | Android (signed off-GitHub, see below) |

Before bumping the version, change it in `src/branding.rs` (`PRODUCT_VERSION`),
`flutter/lib/consts.dart` (`kTfaProductVersion`), `flutter/pubspec.yaml` and `VERSION` in
`tfa-build.yml`.

## Signing

Signing keys are never stored in this repository.

* **Windows**: unsigned for now (customers see a SmartScreen "More info > Run anyway" prompt).
  To switch on Azure Artifact Signing: add the six `AZURE_*` secrets listed in `tfa-build.yml` and set
  the repository variable `WINDOWS_SIGNING` to `azure`. Nothing else changes.
* **macOS**: `tfa/macos/sign_and_notarize.sh` signs with the Developer ID Application certificate and
  notarises with Apple, on our Mac. (CI can do it instead if the `MACOS_*`/`APPLE_API_*` secrets are set.)
* **Android**: `tfa/android/sign_and_publish.sh` signs the CI-built APK with our keystore and attaches it
  to the release.

## Re-branding after an upstream update

`python3 tfa/brand/make_icons.py` regenerates every icon from the SVGs in `tfa/brand/`
(needs `rsvg-convert`, Pillow and the Geist font). Search for `Thinking Fish Assist` comments in
`src/` and `flutter/` for the handful of code changes to carry forward.

The original upstream README is in [docs/README-RustDesk-upstream.md](docs/README-RustDesk-upstream.md).
