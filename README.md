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

### Two names, on purpose

People see **Thinking Fish Assist** everywhere: window titles, tray, About, the Windows Start
menu and desktop shortcuts, Apps & features, the installer, the macOS Finder/Dock/menu bar name
(via `flutter/macos/Runner/en.lproj/InfoPlist.strings`), the DMG volume, the Android launcher,
and the download file names (`Thinking-Fish-Assist-...`; GitHub turns spaces in asset names
into dots, so hyphens).

Internally the app is **`ThinkingFishAssist`** (no spaces), because upstream builds unquoted
command lines and paths from it: the Windows service name, `C:\Program Files\ThinkingFishAssist`,
the config directory (which holds each machine's ID and password, so renaming it would orphan
every install), the `thinkingfishassist://` URI scheme, `/Applications/ThinkingFishAssist.app`
and its launchd plists. `src/branding.rs` holds both (`APP_NAME`, `DISPLAY_NAME`).

## Icons and logo

Andrew's design (26 Sep 2026, `tfa/brand/reference/`) redrawn as SVG by
`tfa/brand/draw_brand.py`; `tfa/brand/make_icons.py` renders every platform's icons from it.
App icons use the mark only (headset + swoosh); the full logo with the wordmark is used in the
About box, the MSI installer and on the website.

## Server

The client talks to a self-hosted open-source RustDesk server (`hbbs`/`hbbr` 1.1.16) and the
MIT-licensed [rustdesk-api](https://github.com/lejianwen/rustdesk-api) for staff logins, the shared
address book and the device list. No RustDesk Server Pro licence is involved.

## Building a release

Push a tag `vX.Y.Z` (or run **Actions > Thinking Fish Assist release** by hand with a test tag).
The workflow builds everything and attaches it to a GitHub release:

| File | What |
|---|---|
| `Thinking-Fish-Assist-windows-x64.exe` | Run-or-install (runs without installing; has an Install button) |
| `Thinking-Fish-Assist-windows-x64.msi` | For managed/silent installs (`msiexec /i ... /qn`) |
| `Thinking-Fish-Assist-macos-aarch64.dmg` / `-x86_64.dmg` | Apple silicon / Intel Macs |
| `Thinking-Fish-Assist-android.apk` | Android (signed off-GitHub, see below) |

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
