# Setup

## On a Linux notebook

```bash
cp .env.example .env
./scripts/install_host_deps.sh   # installs Docker only — review the script first
./scripts/generate_secrets.sh
docker compose up -d --build
```

`docker compose` auto-detects the active network interface and LAN CIDR
unless you set `NETSENTINEL_IFACE` / `NETSENTINEL_LAN_CIDR` in `.env`.

## Migrating to a Raspberry Pi

1. Flash Raspberry Pi OS (64-bit, arm64) — 64-bit is required for the
   container images used here.
2. Install Docker on the Pi the same way as `scripts/install_host_deps.sh`
   does (`sudo apt install docker.io docker-compose-plugin` on Raspberry Pi
   OS, or use Docker's official convenience script).
3. Copy the whole `netsentinel/` directory to the Pi (`rsync -av` or `scp`),
   **including your `.env`** (it already has your generated secrets — don't
   run `generate_secrets.sh` again unless you want a fresh admin password).
4. On the Pi, run:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.rpi.yml up -d --build
   ```
   The `.rpi.yml` override sets conservative resource limits (Suricata and
   nmap are the heaviest components) and pins arm64-compatible base images.
5. Same as the notebook: dashboard at `http://<pi-ip>` (port 80), TUI works
   great over SSH into the Pi.

## Backups

Everything lives in one file: `backend/data/netsentinel.db` (SQLite, WAL
mode — also check for `-wal`/`-shm` sidecar files and copy them together, or
stop the stack first with `docker compose stop backend` for a clean copy).
`cp -r backend/data/ /somewhere/safe/` is a complete backup.

## TLS

There's no TLS in Phase 1 — the dashboard and its login cookie travel as
plain HTTP on your LAN. Acceptable for now since it never leaves your LAN,
but if you want to close that gap later, the simplest add-on is putting
[Caddy](https://caddyserver.com/) in front of the frontend container with a
self-signed certificate (or Tailscale/a private CA if you want the browser
to trust it without warnings) — a small addition to docker-compose.yml, no
app code changes needed.

## Troubleshooting

**Login fails right after setup even with the right password.** `docker
compose` interpolates `$` in `.env` values (both as its own project env file
and when passed through `env_file:`), so a raw bcrypt hash like
`$2b$12$...` gets silently truncated to `$2b$12` by the time the backend
container sees it. `scripts/generate_secrets.sh` and `backend/app/gen_hash.py`
already escape every `$` to `$$` to work around this — if you ever paste a
hash into `.env` by hand, double the dollar signs yourself, or re-run
`generate_secrets.sh`.

## Things that do NOT change between notebook and Pi

- No router configuration, on either.
- No agents on other devices, on either.
- Same `.env` structure, same Docker Compose file (plus the `.rpi.yml`
  overlay), same SQLite file format — you can literally copy
  `backend/data/netsentinel.db` over to keep your history if you migrate.
