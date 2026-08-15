#!/usr/bin/env bash
# Detects the active network interface and LAN CIDR and writes them into
# .env as NETSENTINEL_IFACE / NETSENTINEL_LAN_CIDR. Read-only against the
# system (just inspects existing routes), never touches router config.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found — copy .env.example to .env first."
  exit 1
fi

IFACE=$(ip -o route show default | awk '{print $5; exit}')
if [ -z "$IFACE" ]; then
  echo "Could not auto-detect the default interface. Set NETSENTINEL_IFACE manually in .env." >&2
  exit 1
fi

CIDR=$(ip -o -4 addr show dev "$IFACE" | awk '{print $4; exit}')
if [ -z "$CIDR" ]; then
  echo "Could not auto-detect the IPv4 CIDR for $IFACE. Set NETSENTINEL_LAN_CIDR manually in .env." >&2
  exit 1
fi

# Normalize to network address (e.g. 192.168.1.42/24 -> 192.168.1.0/24) using python3.
NETWORK_CIDR=$(python3 - "$CIDR" <<'PYEOF'
import ipaddress, sys
print(ipaddress.ip_network(sys.argv[1], strict=False))
PYEOF
)

tmp=$(mktemp)
sed \
  -e "s#^NETSENTINEL_IFACE=.*#NETSENTINEL_IFACE=${IFACE}#" \
  -e "s#^NETSENTINEL_LAN_CIDR=.*#NETSENTINEL_LAN_CIDR=${NETWORK_CIDR}#" \
  .env > "$tmp"
mv "$tmp" .env

echo "Detected interface: $IFACE"
echo "Detected LAN CIDR:   $NETWORK_CIDR"
echo "Written to .env."
