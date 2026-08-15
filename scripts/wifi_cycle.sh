#!/usr/bin/env bash
# Runs on a systemd timer (see netsentinel-wifi-cycle.timer/.service in this
# same directory). Only useful if your router runs a dual-band setup as two
# separate SSIDs (common on older/consumer routers without band-steering).
# Every couple of hours, parks this notebook's Wi-Fi on the secondary SSID
# just long enough for NetSentinel's own discovery loop (which re-detects
# interface/CIDR/SSID on every scan — see app/collectors/net_utils.py) to
# pick up its devices and a sample of this host's own traffic there, then
# returns to the primary SSID.
#
# Switching networks only affects THIS notebook's own connectivity — other
# devices on either network are completely unaffected and keep full speed.
#
# Uses NetworkManager connection profiles that are already saved on this
# machine (no Wi-Fi password needed here). Requires NETSENTINEL_PRIMARY_SSID,
# NETSENTINEL_SECONDARY_SSID and NETSENTINEL_WIFI_IFACE to be set to your own
# network's values — there is no sane default, so the script refuses to run
# without them.
set -euo pipefail

PRIMARY_SSID="${NETSENTINEL_PRIMARY_SSID:?set NETSENTINEL_PRIMARY_SSID to your primary Wi-Fi SSID}"
SECONDARY_SSID="${NETSENTINEL_SECONDARY_SSID:?set NETSENTINEL_SECONDARY_SSID to your secondary Wi-Fi SSID}"
WIFI_IFACE="${NETSENTINEL_WIFI_IFACE:?set NETSENTINEL_WIFI_IFACE to your Wi-Fi interface name, e.g. wlan0}"
DWELL_SECONDS="${NETSENTINEL_SECONDARY_DWELL_SECONDS:-300}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

current_ssid() {
  iw dev "${WIFI_IFACE}" link 2>/dev/null | awk -F': ' '/SSID:/{print $2}'
}

refresh_mdns_alias() {
  # netsentinel.local (published by netsentinel-mdns-alias.service) only
  # announces the IP it had at start, so it needs a kick after every
  # network switch to pick up the new address.
  systemctl --user restart netsentinel-mdns-alias.service 2>/dev/null || true
}

log "Switching to secondary network: ${SECONDARY_SSID}"
nmcli connection up "${SECONDARY_SSID}"

sleep 3
if [ "$(current_ssid)" != "${SECONDARY_SSID}" ]; then
  log "WARNING: did not confirm connection to ${SECONDARY_SSID}, aborting cycle (staying on whatever is currently connected)."
  exit 1
fi
refresh_mdns_alias

log "On ${SECONDARY_SSID}. Collecting for ${DWELL_SECONDS}s (NetSentinel's own discovery loop handles the scan)."
sleep "${DWELL_SECONDS}"

log "Switching back to primary network: ${PRIMARY_SSID}"
nmcli connection up "${PRIMARY_SSID}"

sleep 3
refresh_mdns_alias
log "Now on: $(current_ssid)"
