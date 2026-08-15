#!/usr/bin/env bash
# Keeps "netsentinel.local" resolvable to this host's current Wi-Fi IP,
# independent of the machine's own hostname.
# Run as a long-lived process by netsentinel-mdns-alias.service — if it
# exits, the record disappears, so it must keep running (that's how
# avahi-publish works: no separate daemon-side "keep alive" for this).
#
# Restarted by wifi_cycle.sh after every primary/secondary SSID switch, since avahi-publish
# only announces the IP it was given at start and won't notice a later
# address change on its own.
set -euo pipefail

IFACE="${NETSENTINEL_IFACE:-wlp2s0}"
ALIAS="${NETSENTINEL_MDNS_ALIAS:-netsentinel.local}"

IP=""
for _ in $(seq 1 30); do
  IP=$(ip -4 -o addr show "$IFACE" scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1)
  [ -n "$IP" ] && break
  sleep 2
done

if [ -z "$IP" ]; then
  echo "No IPv4 address on ${IFACE} after waiting, giving up." >&2
  exit 1
fi

echo "Publishing ${ALIAS} -> ${IP} on ${IFACE}"
exec avahi-publish -a -R "$ALIAS" "$IP"
