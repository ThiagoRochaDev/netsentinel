#!/bin/sh
# Patches the checked-in suricata.yaml template with the interface/HOME_NET
# from the environment (set in .env by scripts/detect_interface.sh), fetches
# the Emerging Threats Open ruleset on first run, then execs Suricata.
set -eu

: "${NETSENTINEL_IFACE:?Set NETSENTINEL_IFACE in .env — run scripts/detect_interface.sh}"
HOME_NET_VALUE="${NETSENTINEL_LAN_CIDR:-192.168.0.0/16,10.0.0.0/8,172.16.0.0/12}"

CONFIG_SRC=/etc/suricata/suricata.yaml.template
CONFIG_OUT=/etc/suricata/suricata.yaml

sed \
  -e "s#__NETSENTINEL_IFACE__#${NETSENTINEL_IFACE}#g" \
  -e "s#__NETSENTINEL_HOME_NET__#${HOME_NET_VALUE}#g" \
  "$CONFIG_SRC" > "$CONFIG_OUT"

mkdir -p /var/lib/suricata/rules
if [ ! -f /var/lib/suricata/rules/suricata.rules ]; then
  echo "First run: fetching Emerging Threats Open ruleset (needs internet access, no router involved)..."
  suricata-update --no-test || echo "suricata-update failed — continuing with local rules only."
fi

exec suricata -c "$CONFIG_OUT" --af-packet -v
