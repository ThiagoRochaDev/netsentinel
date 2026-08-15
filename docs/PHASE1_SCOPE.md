# Phase 1 Scope — Read this before touching alert rules or collectors

NetSentinel monitors your **own network** for security purposes. To keep that
legitimate and safe, Phase 1 has hard boundaries. If you're extending this
project, do not cross them without deliberately updating this document and
thinking through the consequences again.

## What Phase 1 does

- Deep packet/connection-level inspection (via Suricata) of traffic to/from
  **the machine NetSentinel runs on** — this notebook today, a Raspberry Pi
  later.
- Passive and light-active discovery of every device on your LAN:
  IP, MAC, vendor, hostname, open ports, first/last seen — via ARP, mDNS/SSDP,
  and optional manual nmap scans.
- Rule-based alerting on the above (new devices, newly opened ports, Suricata
  signature hits, anomalous connection volume from this host, etc.)
- A web dashboard and a terminal UI to view all of it.

## What Phase 1 deliberately does NOT do

- **No ARP spoofing, DNS spoofing, or any MITM technique.** We never
  intercept or redirect other devices' traffic.
- **No monitor-mode Wi-Fi capture, no deauth attacks.** The Wi-Fi interface
  stays in normal managed mode, which by construction only sees frames
  addressed to this host plus broadcast/multicast — that's what keeps other
  devices' traffic content out of scope, as a property of the radio mode,
  not just a policy we promise to follow.
- **No router login, no router configuration changes, no use of router
  credentials.** Router integration (client lists, per-device bandwidth) is
  Phase 2, and it happens together with the user after inspecting the real
  admin UI — never silently.
- **No agents on other devices.** Phones, laptops, IoT — nothing gets
  installed on them. Visibility is network-level only.
- **No external notification integrations** (email/push/Telegram). Alerts
  live in the platform.

## Why this matters

The user explicitly rejected MITM/traffic-interception approaches because of
the risk to network stability and because it crosses from "monitoring my own
equipment" into "intercepting my family/guests' traffic," which is a
different (and much more sensitive) thing even on a network you administer.
Keep it that way unless a future, explicit conversation changes the scope.
