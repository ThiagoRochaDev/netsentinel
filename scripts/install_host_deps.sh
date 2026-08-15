#!/usr/bin/env bash
# Installs the ONLY host-level dependency NetSentinel needs: Docker.
# Everything else (Python, Node, Suricata, nmap, scapy) runs inside containers —
# nothing else touches this machine's package set, and NOTHING touches your
# router or network configuration.
#
# This script is meant to be reviewed before running, not blindly piped into bash.
set -euo pipefail

echo "This will run:"
echo "  sudo pacman -S --needed docker docker-compose"
echo "  sudo systemctl enable --now docker"
echo "  sudo usermod -aG docker \$USER"
echo
echo "Note: membership in the 'docker' group is effectively root-equivalent"
echo "access to this machine (containers can mount the host filesystem)."
echo "You will need to log out/in (or reboot) for the group change to apply."
echo
read -r -p "Proceed? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted. Nothing was installed."
  exit 1
fi

sudo pacman -S --needed docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

echo
echo "Docker installed and enabled. Log out and back in (or run 'newgrp docker')"
echo "for the group membership to take effect, then verify with: docker ps"
