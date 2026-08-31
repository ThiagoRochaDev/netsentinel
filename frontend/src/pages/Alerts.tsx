import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { useSearchParams } from "react-router";
import { api, type Alert } from "../api/client";
import { SeverityBadge } from "../components/SeverityBadge";
import { debounce } from "../utils/debounce";
import { useLiveSocket } from "../ws/useLiveSocket";

const STATUS_LABEL: Record<Alert["status"], string> = {
  new: "Novo",
  ack: "Reconhecido",
  resolved: "Resolvido",
};

export function Alerts() {
  const [searchParams] = useSearchParams();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>(() => searchParams.get("status") ?? "");
  const [severityFilter, setSeverityFilter] = useState<string>(() => searchParams.get("severity") ?? "");

  function load() {
    api
      .alerts({ status: statusFilter || undefined, severity: severityFilter || undefined })
      .then(setAlerts)
      .catch(() => {});
  }

  useEffect(load, [statusFilter, severityFilter]);
  // Debounced: a burst of many alerts arriving over the WebSocket in a
  // short window (e.g. a noisy signature before it's rate-limited
  // server-side) must not trigger one API refetch per message.
  const debouncedLoad = useMemo(() => debounce(load, 1000), [statusFilter, severityFilter]);
  useLiveSocket((msg) => {
    if (msg.type === "new_alert") debouncedLoad();
  });

  async function updateStatus(alert: Alert, status: Alert["status"]) {
    const updated = await api.patchAlert(alert.id, status);
    setAlerts((prev) => prev.map((a) => (a.id === alert.id ? updated : a)));
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div>
        <h1 style={{ fontSize: 22, margin: 0 }}>Alertas</h1>
        <div className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>
          Tudo que o motor de detecção encontrou de suspeito
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Todos os status</option>
          <option value="new">Novo</option>
          <option value="ack">Reconhecido</option>
          <option value="resolved">Resolvido</option>
        </select>
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
          <option value="">Toda severidade</option>
          <option value="high,critical">Graves (alto + crítico)</option>
          <option value="critical">Crítico</option>
          <option value="high">Alto</option>
          <option value="medium">Médio</option>
          <option value="low">Baixo</option>
          <option value="info">Info</option>
        </select>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {alerts.length === 0 && <div className="text-muted">Nenhum alerta encontrado.</div>}
        {alerts.map((a) => (
          <div key={a.id} className="card" style={{ padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{a.title}</div>
                <div className="text-muted" style={{ fontSize: 12, marginTop: 2 }}>
                  {new Date(a.ts).toLocaleString("pt-BR")} · {a.rule_key} · fonte: {a.source}
                </div>
              </div>
              <SeverityBadge severity={a.severity} />
            </div>
            <div className="text-secondary" style={{ fontSize: 13 }}>
              {a.description}
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span className="text-muted" style={{ fontSize: 12 }}>
                {STATUS_LABEL[a.status]}
              </span>
              {a.status !== "ack" && (
                <button onClick={() => updateStatus(a, "ack")} style={buttonStyle}>
                  Reconhecer
                </button>
              )}
              {a.status !== "resolved" && (
                <button onClick={() => updateStatus(a, "resolved")} style={buttonStyle}>
                  Resolver
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const buttonStyle: CSSProperties = {
  background: "none",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  padding: "4px 10px",
  fontSize: 12,
  color: "var(--text-secondary)",
};
