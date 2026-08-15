import { useEffect, useMemo, useState } from "react";
import { api, type SuricataEvent } from "../api/client";
import { debounce } from "../utils/debounce";
import { useLiveSocket } from "../ws/useLiveSocket";

const EVENT_TYPES = ["", "alert", "dns", "http", "tls", "ssh"];

export function LogsExplorer() {
  const [events, setEvents] = useState<SuricataEvent[]>([]);
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState("");
  const [liveTail, setLiveTail] = useState(true);

  function load() {
    api.events({ search: search || undefined, event_type: eventType || undefined, limit: 300 }).then(setEvents).catch(() => {});
  }

  useEffect(load, [search, eventType]);

  // Debounced: this host can generate several Suricata events per second
  // (every DNS/HTTP/TLS/SSH connection), so live-tail must not refetch on
  // every single WebSocket message.
  const debouncedLoad = useMemo(() => debounce(load, 1000), [search, eventType]);
  useLiveSocket((msg) => {
    if (!liveTail || msg.type !== "suricata_event") return;
    debouncedLoad();
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div>
        <h1 style={{ fontSize: 22, margin: 0 }}>Logs</h1>
        <div className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>
          Todos os eventos vistos pelo Suricata nesta máquina
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <input
          placeholder="Buscar por IP ou assinatura..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ minWidth: 280, flex: "1 1 280px" }}
        />
        <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t || "Todos os tipos"}
            </option>
          ))}
        </select>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }} className="text-secondary">
          <input type="checkbox" checked={liveTail} onChange={(e) => setLiveTail(e.target.checked)} style={{ width: "auto" }} />
          Live tail
        </label>
      </div>

      <div className="card" style={{ overflow: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Quando</th>
              <th>Tipo</th>
              <th>Severidade</th>
              <th>Assinatura / Categoria</th>
              <th>Origem</th>
              <th>Destino</th>
              <th>Proto</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id}>
                <td style={{ whiteSpace: "nowrap" }}>{new Date(e.ts).toLocaleString("pt-BR")}</td>
                <td>{e.event_type}</td>
                <td>{e.severity ?? "-"}</td>
                <td>
                  {e.signature ?? "-"}
                  {e.category && <div className="text-muted" style={{ fontSize: 11 }}>{e.category}</div>}
                </td>
                <td>
                  {e.src_ip ?? "-"}
                  {e.src_port ? `:${e.src_port}` : ""}
                </td>
                <td>
                  {e.dst_ip ?? "-"}
                  {e.dst_port ? `:${e.dst_port}` : ""}
                </td>
                <td>{e.proto ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
