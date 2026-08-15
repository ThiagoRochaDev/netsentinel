# Architecture

```
┌─────────────┐   eve.json (tail)   ┌───────────────────┐
│  Suricata   │────────────────────▶│                    │
│ (af-packet, │                     │   backend (FastAPI)│
│  this host's│   ARP/mDNS/nmap     │   - collectors     │◀── LAN (your Wi-Fi)
│  interface) │────────────────────▶│   - alert_engine   │
└─────────────┘                     │   - REST + WS API  │
                                     │   - SQLite (WAL)   │
                                     └─────────┬──────────┘
                                     REST/WS   │   REST/WS
                              ┌────────────────┴───────────────┐
                              ▼                                 ▼
                     ┌─────────────────┐              ┌──────────────────┐
                     │ frontend (nginx │              │  tui (Textual)   │
                     │ + React SPA)    │              │  terminal client │
                     │ proxies /api,/ws│              └──────────────────┘
                     └─────────────────┘
                              ▲
                    any device on your LAN
                    (browser, after login)
```

## Components

- **suricata/** — IDS/packet-inspection engine. Runs on this host's own
  network interface (`HOME_NET` = this host's IP). Emits structured JSON
  events (`eve.json`) for flows, alerts, and protocol metadata.
- **backend/app/collectors/** — everything that gathers data:
  - `suricata_tail.py` tails `eve.json` and writes to `suricata_events` /
    `connections`.
  - `discovery_arp.py` sends ARP requests / reads the ARP table to find
    devices on the LAN (scapy).
  - `discovery_mdns.py` passively listens for mDNS/SSDP broadcasts
    (device names, service hints).
  - `discovery_portscan.py` — opt-in, manually triggered nmap scan of a
    single device.
  - `oui_lookup.py` — offline IEEE OUI table → MAC vendor name.
- **backend/app/alert_engine/** — rule evaluation over collected data,
  writes to `alerts`, pushes over the WebSocket hub.
- **backend/app/api/** — REST + WebSocket surface consumed by both the
  frontend and the TUI (same API, two clients).
- **frontend/** — React + TypeScript + Vite SPA, dark mode, Apache ECharts
  for graphs. Built inside Docker (Node never touches the host). nginx
  serves the static build and reverse-proxies `/api` and `/ws` to the
  backend so the browser only ever talks to one origin.
- **tui/** — Python Textual terminal app hitting the same API. Works over
  SSH, no GUI required — good fit for a headless Raspberry Pi.

## Data flow boundary (why this is safe)

Suricata and the discovery collectors only ever see: (a) this host's own
traffic (normal managed-mode Wi-Fi doesn't deliver other devices' unicast
frames), and (b) broadcast/multicast + ARP replies from other devices, which
reveal presence/IP/MAC but not traffic content. See
[PHASE1_SCOPE.md](PHASE1_SCOPE.md) for the full boundary statement.

## Storage

SQLite with WAL mode, single writer queue shared by all collectors and the
alert engine (avoids lock contention). See the plan doc for the table list.
Chosen over Postgres/Timescale for zero operational overhead on a Raspberry
Pi — no separate DB service to run, patch, or lose to an SD-card power loss.
