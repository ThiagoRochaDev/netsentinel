import { useEffect, useState } from "react";
import { api, type Connection, type ConnectionStats } from "../api/client";
import { CategoryBarChart } from "../components/charts/CategoryBarChart";
import { StatTile } from "../components/StatTile";
import { useLiveSocket } from "../ws/useLiveSocket";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

export function Traffic() {
  const [stats, setStats] = useState<ConnectionStats | null>(null);
  const [recent, setRecent] = useState<Connection[]>([]);

  function load() {
    api.connectionStats().then(setStats).catch(() => {});
    api.connections({ limit: 50 }).then(setRecent).catch(() => {});
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 15_000);
    return () => clearInterval(interval);
  }, []);

  useLiveSocket((msg) => {
    if (msg.type === "flow_tick") {
      // Live ticks arrive far more often than the DB-backed table needs a
      // full reload for; the 15s poll above keeps the table fresh enough.
    }
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22, margin: 0 }}>Tráfego</h1>
        <div className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>
          Conexões desta máquina, capturadas pelo Suricata
        </div>
      </div>

      <div className="kpi-grid">
        <StatTile label="Total transferido (últimos registros)" value={stats ? formatBytes(stats.total_bytes) : "--"} />
        <StatTile label="Destinos distintos" value={stats?.top_talkers.length ?? "--"} />
        <StatTile label="Protocolos distintos" value={stats ? Object.keys(stats.protocols).length : "--"} />
      </div>

      <div className="two-col-grid">
        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Top destinos por volume</div>
          {stats && (
            <CategoryBarChart
              data={stats.top_talkers.map((t) => ({ label: t.ip, value: t.bytes }))}
              colorIndex={0}
              valueFormatter={formatBytes}
            />
          )}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Protocolos</div>
          {stats && (
            <CategoryBarChart
              data={Object.entries(stats.protocols).map(([label, value]) => ({ label, value }))}
              colorIndex={2}
            />
          )}
        </div>
      </div>

      <div className="card" style={{ overflow: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Quando</th>
              <th>Origem</th>
              <th>Destino</th>
              <th>Proto</th>
              <th>App</th>
              <th>Bytes</th>
            </tr>
          </thead>
          <tbody>
            {recent.map((c) => (
              <tr key={c.id}>
                <td>{new Date(c.ts).toLocaleTimeString("pt-BR")}</td>
                <td>
                  {c.src_ip}
                  {c.src_port ? `:${c.src_port}` : ""}
                </td>
                <td>
                  {c.dst_ip}
                  {c.dst_port ? `:${c.dst_port}` : ""}
                </td>
                <td>{c.proto}</td>
                <td>{c.app_proto ?? "-"}</td>
                <td>{formatBytes(c.bytes_in + c.bytes_out)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
