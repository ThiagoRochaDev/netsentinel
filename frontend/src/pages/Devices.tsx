import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { api, type Device } from "../api/client";
import { useLiveSocket } from "../ws/useLiveSocket";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "agora";
  if (mins < 60) return `${mins}min atrás`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h atrás`;
  return `${Math.round(hours / 24)}d atrás`;
}

export function Devices() {
  const [searchParams, setSearchParams] = useSearchParams();
  const onlineOnly = searchParams.get("online") === "1";
  const [devices, setDevices] = useState<Device[]>([]);
  const [search, setSearch] = useState("");
  const [scanning, setScanning] = useState<number | null>(null);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [triggeringDiscovery, setTriggeringDiscovery] = useState(false);

  function load() {
    api
      .devices(onlineOnly ? { online: true } : undefined)
      .then(setDevices)
      .catch(() => {});
  }

  useEffect(load, [onlineOnly]);
  useLiveSocket((msg) => {
    if (msg.type === "new_device") load();
  });

  function toggleOnlineOnly() {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (onlineOnly) next.delete("online");
      else next.set("online", "1");
      return next;
    });
  }

  async function handleRename(device: Device) {
    const name = window.prompt("Nome para este dispositivo:", device.custom_name ?? "");
    if (name === null) return;
    const updated = await api.patchDevice(device.id, { custom_name: name });
    setDevices((prev) => prev.map((d) => (d.id === device.id ? updated : d)));
  }

  async function handleToggleKnown(device: Device) {
    const updated = await api.patchDevice(device.id, { is_known: !device.is_known });
    setDevices((prev) => prev.map((d) => (d.id === device.id ? updated : d)));
  }

  async function handlePortscan(device: Device) {
    setScanning(device.id);
    setScanResult(null);
    try {
      const result = await api.triggerPortscan(device.id);
      setScanResult(
        result.open_ports.length
          ? `${device.mac_address}: portas abertas ${result.open_ports.map((p) => `${p.port}/${p.proto}`).join(", ")}`
          : `${device.mac_address}: nenhuma porta aberta encontrada.`
      );
    } catch (err) {
      setScanResult(err instanceof Error ? err.message : "Falha no scan.");
    } finally {
      setScanning(null);
    }
  }

  async function handleDiscovery() {
    setTriggeringDiscovery(true);
    try {
      await api.triggerDiscovery();
      load();
    } finally {
      setTriggeringDiscovery(false);
    }
  }

  const filtered = devices.filter((d) => {
    const q = search.toLowerCase();
    return (
      !q ||
      d.mac_address.toLowerCase().includes(q) ||
      (d.custom_name ?? "").toLowerCase().includes(q) ||
      (d.hostname ?? "").toLowerCase().includes(q) ||
      (d.current_ip ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>Dispositivos</h1>
          <div className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>
            {devices.length} dispositivo{devices.length === 1 ? "" : "s"} {onlineOnly ? "online agora" : "vistos na rede"}
          </div>
        </div>
        <button
          onClick={handleDiscovery}
          disabled={triggeringDiscovery}
          style={{
            background: "var(--series-1)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius-sm)",
            padding: "9px 14px",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          {triggeringDiscovery ? "Escaneando..." : "Escanear rede agora"}
        </button>
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <input
          placeholder="Buscar por MAC, nome, hostname ou IP..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 360, width: "100%", flex: "1 1 280px" }}
        />
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }} className="text-secondary">
          <input type="checkbox" checked={onlineOnly} onChange={toggleOnlineOnly} style={{ width: "auto" }} />
          Somente online agora
        </label>
      </div>

      {scanResult && (
        <div className="card" style={{ padding: "10px 14px", fontSize: 13 }}>
          {scanResult}
        </div>
      )}

      <div className="card" style={{ overflow: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>MAC</th>
              <th>IP atual</th>
              <th>Fabricante</th>
              <th>Hostname</th>
              <th>Visto por último</th>
              <th>Conexão</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.id}>
                <td>
                  <button
                    onClick={() => handleRename(d)}
                    style={{ background: "none", border: "none", color: "var(--text-primary)", padding: 0, font: "inherit", textAlign: "left" }}
                  >
                    {d.custom_name || <span className="text-muted">sem nome</span>}
                  </button>
                </td>
                <td style={{ fontFamily: "monospace" }}>{d.mac_address}</td>
                <td>{d.current_ip ?? "-"}</td>
                <td>{d.vendor_oui ?? "-"}</td>
                <td>{d.hostname ?? "-"}</td>
                <td>{timeAgo(d.last_seen)}</td>
                <td>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                    <span
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: d.is_online ? "var(--status-good)" : "var(--text-muted)",
                        flexShrink: 0,
                      }}
                    />
                    <span className={d.is_online ? undefined : "text-muted"}>{d.is_online ? "Online" : "Offline"}</span>
                  </span>
                </td>
                <td>
                  <button
                    onClick={() => handleToggleKnown(d)}
                    style={{
                      background: "none",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                      padding: "3px 8px",
                      fontSize: 12,
                      color: d.is_known ? "var(--status-good)" : "var(--status-warning)",
                    }}
                  >
                    {d.is_known ? "Conhecido" : "Desconhecido"}
                  </button>
                </td>
                <td>
                  <button
                    onClick={() => handlePortscan(d)}
                    disabled={scanning === d.id}
                    style={{
                      background: "none",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                      padding: "4px 10px",
                      fontSize: 12,
                      color: "var(--text-secondary)",
                    }}
                  >
                    {scanning === d.id ? "Escaneando..." : "Ver portas"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
