#!/usr/bin/env bash
# Manually refreshes the Emerging Threats Open ruleset inside the running
# suricata container. Runs automatically on first boot too (see
# suricata/entrypoint.sh) — use this later to pull updates.
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose exec suricata suricata-update
docker compose restart suricata
echo "Rules updated and Suricata restarted."
