# Thinking Fish Assist: server runbook

No secrets here. Credentials are in the Thinking Fish vault (`services/thinking-fish-assist.md`).

## Layout

| Item | Value |
|---|---|
| Host | AWS Lightsail `tf-assist`, eu-west-2a, `nano_3_0` ($5/month: 512 MB RAM, 2 vCPU burst, 20 GB SSD, 1 TB transfer), Ubuntu 24.04, 1 GB swap |
| Address | static IP `35.179.247.106`, DNS `assist.thinkingfish.com` (A record in the thinkingfish.com zone on our cPanel DNS) |
| Firewall (Lightsail) | TCP 21115-21119 and UDP 21116 from anywhere; TCP 80/443 (console, Let's Encrypt); TCP 22 from the Thinking Fish admin host only |
| `tfassist-hbbs` | ID/rendezvous server, RustDesk server OSS 1.1.16 (`/opt/tfassist/bin/hbbs -r assist.thinkingfish.com:21117 -k _`) |
| `tfassist-hbbr` | relay server (`hbbr -k _`) |
| Key pair | `/var/lib/tfassist/id_ed25519{,.pub}`; `-k _` makes both servers refuse clients without our key |
| `tfassist-api` | lejianwen/rustdesk-api v2.7 (MIT) in `/opt/rustdesk-api`, listening on 127.0.0.1:21114, SQLite in `data/` |
| `caddy` | HTTPS for the console/API (Let's Encrypt, auto-renew), `/etc/caddy/Caddyfile`; swagger and the web client paths are blocked |

All services are systemd units with `Restart=always`, run as unprivileged users and are sandboxed
(`ProtectSystem=strict`, `NoNewPrivileges`). Ubuntu unattended-upgrades applies security patches.

**THE KEY PAIR IS BAKED INTO EVERY INSTALLED CLIENT.** If it is lost or changed, every copy in the field
stops connecting. It is backed up in the vault and in every backup below. On any rebuild, restore it exactly.

## Backups

1. Lightsail automatic daily snapshot at 03:00 (7 kept) + manual snapshot `tf-assist-initial-20260926`.
2. Weekly off-site copy (Sunday 02:15) of `/var/lib/tfassist`, `/opt/rustdesk-api`, `/etc/caddy`,
   `/opt/tfassist` and the unit files to the locked DR account bucket (claudia-scripts `dr/lightsail-app-dr.sh`).
3. Key pair also in the vault.

## Monitoring

`bin/tf_assist_health.py` on the Thinking Fish admin host runs every 5 minutes: TCP 21115/21116/21117,
UDP 21116 and the HTTPS console (certificate > 14 days). It sends one Telegram message when the state
changes (down, then recovered). Log: `~/tf-assist/health.log`.

## Common jobs

```bash
ssh tf-assist
systemctl status tfassist-hbbs tfassist-hbbr tfassist-api caddy
journalctl -u tfassist-hbbs -n 100          # registrations, punch/relay requests
sudo tail -f /opt/rustdesk-api/runtime/log.txt
```

* **Upgrade hbbs/hbbr**: download the new `rustdesk-server-linux-amd64.zip` from rustdesk/rustdesk-server
  releases, replace the two binaries in `/opt/tfassist/bin`, restart both units. The key is untouched.
* **Upgrade the API**: take a snapshot, replace `/opt/rustdesk-api/apimain` and `resources/` from the new
  release, keep `conf/` and `data/`, restart. The project has had no release since v2.7 (Sep 2025): check
  for a maintained fork before upgrading, and test client sign-in afterwards.
* **Reset the console break-glass admin password**: stop `tfassist-api`, run
  `sudo -u tfapi ./apimain reset-admin-pwd <new>` in `/opt/rustdesk-api`, start it again.
* **Rebuild from scratch**: new Lightsail nano Ubuntu 24.04, attach static IP `tf-assist-ip`, restore the
  latest DR tarball over `/` (it contains the unit files), `apt install caddy sqlite3`, create users
  `tfassist` and `tfapi`, `systemctl enable --now tfassist-hbbs tfassist-hbbr tfassist-api caddy`.

## Cost

About $5.20 a month (£3.90): the $5 plan (IPv4 and 1 TB transfer included) plus a few pence of snapshot
storage ($0.05/GB-month, incremental). Relay traffic beyond 1 TB would be $0.09/GB; a relayed support
session uses roughly 0.5 to 2 GB an hour, so 1 TB covers hundreds of hours a month.
