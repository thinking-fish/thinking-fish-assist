# Replacing AnyDesk with Thinking Fish Assist

Status 26 September 2026. "Covered" means available in Thinking Fish Assist today with no paid licence.

## Feature checklist

| AnyDesk feature | Thinking Fish Assist | Notes |
|---|---|---|
| Attended support (customer reads ID, clicks Accept) | Covered | Same flow. The ID is 9 digits; the customer clicks Accept, no password needed. |
| Unattended access | Covered | Windows service (works at the login screen), macOS daemon, permanent password per device, optional TOTP 2FA on the device. |
| Windows, macOS, Linux, Android as the controlled side | Covered | We ship Windows x64, macOS (Apple silicon + Intel) and Android. Linux is supported by the code but not built yet (add to CI if a customer needs it). |
| iPhone / iPad | Controller only | Same as AnyDesk: Apple does not allow iOS devices to be controlled. Our iOS app is not published (low priority). |
| File transfer | Covered | File manager in session, plus copy/paste of files on Windows and macOS. |
| Chat | Covered | In-session text chat. |
| Voice | Covered | In-session voice call. |
| Session recording | Covered (local) | Recorded on the engineer's (or customer's) computer, manually or automatically; not stored centrally. AnyDesk is the same unless you pay for its cloud features. |
| Multi-monitor, Ctrl+Alt+Del, restart and reconnect | Covered | |
| Privacy mode / black screen, block user input | Covered (Windows) | |
| Remote printing | Covered (Windows) | Optional printer driver. |
| TCP tunnel / RDP over the session | Covered | |
| Wake-on-LAN | Partial | Works only via another online device on the same network. |
| Address book shared across the team | Covered | rustdesk-api console: address books shared with a staff group, tags, aliases. |
| Staff accounts + MFA | Covered | Sign in with Microsoft (Entra, our tenant's MFA). Only people assigned to the Entra app can sign in. |
| Device list / online status | Covered | Console device list (every installed copy that reaches our server). |
| Audit: who connected where and when | Covered | Console connection log, file-transfer log, staff login log. |
| Custom-branded client, our own server | Covered | Our name, logo and colours; our London server and key are built in. |
| MSI / silent deployment | Covered | MSI with properties, `--silent-install`, `--password`, `--get-id`. |
| Signed Windows installer | Not yet | Unsigned by decision: SmartScreen shows "More info > Run anyway" (explained on the download page). Switch on Azure Artifact Signing (about £8/month) with one repository setting if customers push back. |
| Signed + notarised Mac app | Pending | Needs Andrew (Apple Account Holder) to create a Developer ID Application certificate; CSR ready in the vault. Until then Mac users click "Open Anyway" in Privacy & Security once. |
| Session reports / time tracking for billing | Gap | AnyDesk's paid session reports have no equivalent; use the console connection log (start/end times per ID). |
| Mobile app for staff (control from phone) | Covered (Android) | Android app can control computers; iOS controller not published. |
| Vendor support / SLA | Gap | Community-supported open source; we maintain it ourselves. The console add-on has had no release since Sep 2025 (see risks). |

## Risks we accept

* **Console add-on is unmaintained upstream** (lejianwen/rustdesk-api, MIT, last release v2.7, Sep 2025).
  The core connection path (hbbs/hbbr, maintained by RustDesk) does not depend on it; if it breaks, sessions
  still work and we lose only sign-in, shared address books and logs. Mitigations: HTTPS only, swagger and web
  client off, registration off, captcha + IP ban on failed logins, staff sign in through Microsoft MFA,
  strong break-glass admin in the vault, daily snapshots. Re-check for a maintained fork before upgrading.
* **We own the upgrades**: new RustDesk releases need a rebuild of our client (tag a release; CI does the rest).
* **Unsigned Windows installer**: some corporate endpoint protection may block unsigned executables. If a
  customer's IT blocks it, turn on signing (above).

## Migration plan

1. **Weeks 1-2 (now)**: staff install Thinking Fish Assist and sign in. Use it first for customers already on
   the phone; keep AnyDesk as the fallback. The support page now offers Assist first, AnyDesk second.
2. **Weeks 2-4**: during routine work, install Assist unattended on managed machines alongside AnyDesk; add each
   to the shared address book. Tell contract customers (short email) that we are moving.
3. **Week 4-6**: when every managed machine is in the Assist address book and has been connected to at least once,
   stop using AnyDesk for new sessions.
4. **Switch-off**: remove AnyDesk from managed machines via RMM, remove the AnyDesk link from the support page,
   cancel the AnyDesk licence at its next renewal date.

## Cost

| Item | Cost |
|---|---|
| Server (Lightsail, London) incl. backups | about £3.90/month |
| RustDesk server, console add-on, client | £0 (open source) |
| Build pipeline (GitHub Actions, public repo) | £0 |
| Apple Developer Program | already paid |
| Windows code signing | £0 now; about £8/month (Azure Artifact Signing) only if we switch it on |
| **Unavoidable ongoing cost** | **about £3.90/month** |
