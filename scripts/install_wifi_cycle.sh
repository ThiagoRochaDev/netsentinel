#!/usr/bin/env bash
# Installs the systemd *user* timer that periodically parks this notebook's
# Wi-Fi on your secondary SSID (5 min every 2h by default) so NetSentinel's
# discovery loop can see devices/traffic there too. Requires
# NETSENTINEL_PRIMARY_SSID / NETSENTINEL_SECONDARY_SSID / NETSENTINEL_WIFI_IFACE
# to be set in netsentinel-wifi-cycle.service before installing (see that
# file) — only relevant if your router exposes two separate band SSIDs.
#
# This MUST be a user unit, not a system-wide one: nmcli's network-control
# permissions are granted per logged-in session via polkit, and a
# system-wide service (running outside your session) gets
# "Not authorized to control networking" even when run as your own user.
# A --user unit runs inside your session and inherits that authorization —
# no sudo needed for any of this.
set -euo pipefail
cd "$(dirname "$0")"

USER_UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_UNIT_DIR"
cp netsentinel-wifi-cycle.service netsentinel-wifi-cycle.timer "$USER_UNIT_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now netsentinel-wifi-cycle.timer

# Lets the timer keep firing even if you're not graphically logged in
# (e.g. switched to a text VT) — harmless if it's already enabled.
loginctl enable-linger "$USER" 2>/dev/null || true

echo
echo "Installed as a user service. Check status with:"
echo "  systemctl --user status netsentinel-wifi-cycle.timer"
echo "  systemctl --user list-timers netsentinel-wifi-cycle.timer"
echo "  journalctl --user -u netsentinel-wifi-cycle.service -f"
echo
echo "To stop the cycling: systemctl --user disable --now netsentinel-wifi-cycle.timer"
