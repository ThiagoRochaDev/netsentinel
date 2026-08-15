"""Offline MAC vendor lookup. Ships a small curated table of common
consumer-device vendors so device discovery works with zero network calls.

For a fuller lookup, drop a copy of the IEEE OUI registry (CSV with columns
`Assignment,Organization Name`, e.g. from
https://standards-oui.ieee.org/oui/oui.csv) at backend/app/collectors/oui_full.csv
(gitignored) — it will be preferred automatically if present.
"""

import csv
import functools
from pathlib import Path

_FULL_TABLE_PATH = Path(__file__).parent / "oui_full.csv"

_BUILTIN: dict[str, str] = {
    "00:1A:11": "Google",
    "F4:F5:D8": "Google",
    "3C:5A:B4": "Google",
    "AC:63:BE": "Apple",
    "F0:18:98": "Apple",
    "A4:83:E7": "Apple",
    "00:1E:C2": "Apple",
    "88:63:DF": "Apple",
    "D0:81:7A": "Apple",
    "5C:F9:38": "Apple",
    "F8:FF:C2": "Samsung",
    "8C:79:F5": "Samsung",
    "CC:07:AB": "Samsung",
    "B0:72:BF": "Samsung",
    "18:E8:29": "Samsung",
    "FC:A6:67": "Amazon",
    "68:37:E9": "Amazon",
    "44:65:0D": "Amazon",
    "0C:47:C9": "Amazon",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "E4:5F:01": "Raspberry Pi Foundation",
    "50:C7:BF": "TP-Link",
    "A4:2B:B0": "TP-Link",
    "EC:08:6B": "TP-Link",
    "C0:25:E9": "TP-Link",
    "AC:84:C6": "ASUSTek",
    "1C:87:2C": "ASUSTek",
    "04:D9:F5": "ASUSTek",
    "84:16:F9": "ASUSTek",
    "24:4B:FE": "Intel",
    "3C:A9:F4": "Intel",
    "8C:16:45": "Intel",
    "18:56:80": "Intel",
    "70:85:C2": "Espressif (ESP32/ESP8266 IoT)",
    "24:6F:28": "Espressif (ESP32/ESP8266 IoT)",
    "A4:CF:12": "Espressif (ESP32/ESP8266 IoT)",
    "EC:FA:BC": "Espressif (ESP32/ESP8266 IoT)",
    "B4:E6:2D": "Sonos",
    "5C:AA:FD": "Sonos",
    "94:9F:3E": "Xiaomi",
    "78:11:DC": "Xiaomi",
    "64:09:80": "Xiaomi",
    "00:24:E4": "Withings/Nokia Health",
    "44:07:0B": "Roku",
    "CC:6D:A0": "Roku",
    "40:B4:CD": "Amazon",
    "34:D2:70": "Huawei",
    "F8:98:EF": "Huawei",
    "10:C6:1F": "Huawei",
    "00:E0:4C": "Realtek (generic NIC)",
    "52:54:00": "QEMU/KVM (virtual NIC)",
    "08:00:27": "VirtualBox (virtual NIC)",
    "00:0C:29": "VMware (virtual NIC)",
    "00:50:56": "VMware (virtual NIC)",
    "DC:A6:32": "Raspberry Pi Foundation",
}


@functools.lru_cache(maxsize=1)
def _load_full_table() -> dict[str, str]:
    table: dict[str, str] = {}
    if not _FULL_TABLE_PATH.exists():
        return table
    with _FULL_TABLE_PATH.open(newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            assignment = (row.get("Assignment") or "").strip().upper()
            org = (row.get("Organization Name") or "").strip()
            if len(assignment) == 6:
                oui = f"{assignment[0:2]}:{assignment[2:4]}:{assignment[4:6]}"
                table[oui] = org
    return table


def lookup_vendor(mac_address: str) -> str | None:
    oui = mac_address.upper()[0:8]
    full = _load_full_table()
    if oui in full:
        return full[oui]
    return _BUILTIN.get(oui)
