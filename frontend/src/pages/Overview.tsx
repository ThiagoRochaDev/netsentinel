import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Alert, type Overview as OverviewStats, type Timeseries } from "../api/client";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatTile } from "../components/StatTile";
import { TimeSeriesChart } from "../components/charts/TimeSeriesChart";
import { debounce } from "../utils/debounce";
import { useLiveSocket } from "../ws/useLiveSocket";

export function Overview() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [series, setSeries] = useState<Timeseries | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);

  const load = useCallback(() => {
    api.overview().then(setStats).catch(() => {});
    api.timeseries("connections", "hour", "24h").then(setSeries).catch(() => {});
    api.alerts({ status: "new" }).then((a) => setRecentAlerts(a.slice(0, 8))).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, [load]);

  // Debounced: a burst of many WebSocket messages in a short window must
  // not trigger one API refetch per message.
  const debouncedLoad = useMemo(() => debounce(load, 1000), [load]);
  useLiveSocket((msg) => {
    if (msg.type === "new_alert" || msg.type === "new_device") debouncedLoad();
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22, margin: 0 }}>Overview</h1>
        <div className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>
          Visão geral da sua rede e desta máquina
        </div>
      </div>

      <div className="kpi-grid">
        <StatTile label="Dispositivos" value={stats?.total_devices ?? "--"} onClick={() => navigate("/devices")} />
        <StatTile
          label="Online agora"
          value={stats?.online_devices ?? "--"}
          accent="good"
          onClick={() => navigate("/devices?online=1")}
        />
        <StatTile
          label="Alertas novos"
          value={stats?.new_alerts ?? "--"}
          accent={stats?.new_alerts ? "warning" : "default"}
          onClick={() => navigate("/alerts?status=new")}
        />
        <StatTile
          label="Alertas graves"
          value={stats?.high_severity_alerts ?? "--"}
          accent={stats?.high_severity_alerts ? "critical" : "default"}
          onClick={() => navigate("/alerts?status=new&severity=high,critical")}
        />
        <StatTile label="Eventos Suricata (24h)" value={stats?.events_24h ?? "--"} onClick={() => navigate("/logs")} />
        <StatTile label="Conexões (24h)" value={stats?.connections_24h ?? "--"} onClick={() => navigate("/traffic")} />
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Conexões desta máquina — últimas 24h</div>
        {series && <TimeSeriesChart points={series.points} seriesName="Conexões" colorIndex={0} />}
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Alertas recentes</div>
        {recentAlerts.length === 0 && <div className="text-muted">Nenhum alerta novo.</div>}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {recentAlerts.map((a) => (
            <div
              key={a.id}
              onClick={() => navigate("/alerts?status=new")}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 12,
                alignItems: "baseline",
                cursor: "pointer",
              }}
            >
              <div>
                <div style={{ fontSize: 13.5 }}>{a.title}</div>
                <div className="text-muted" style={{ fontSize: 12 }}>
                  {new Date(a.ts).toLocaleString("pt-BR")}
                </div>
              </div>
              <SeverityBadge severity={a.severity} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
