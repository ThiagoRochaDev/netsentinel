const BASE = ""; // same-origin: dev via Vite proxy, prod via nginx

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: (username: string, password: string) =>
    request<{ username: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  me: () => request<{ username: string }>("/api/auth/me"),

  devices: (params?: { online?: boolean }) => request<Device[]>(`/api/devices${qs(params)}`),
  device: (id: number) => request<Device>(`/api/devices/${id}`),
  patchDevice: (id: number, patch: Partial<Pick<Device, "custom_name" | "is_known">>) =>
    request<Device>(`/api/devices/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deviceSightings: (id: number) => request<Sighting[]>(`/api/devices/${id}/sightings`),
  devicePorts: (id: number) => request<DevicePort[]>(`/api/devices/${id}/ports`),

  alerts: (params?: { status?: string; severity?: string }) =>
    request<Alert[]>(`/api/alerts${qs(params)}`),
  alertStats: () => request<AlertStats>("/api/alerts/stats"),
  patchAlert: (id: number, status: string) =>
    request<Alert>(`/api/alerts/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),

  events: (params?: { search?: string; event_type?: string; limit?: number }) =>
    request<SuricataEvent[]>(`/api/events${qs(params)}`),

  connections: (params?: { src_ip?: string; dst_ip?: string; limit?: number }) =>
    request<Connection[]>(`/api/connections${qs(params)}`),
  connectionStats: () => request<ConnectionStats>("/api/connections/stats"),

  overview: () => request<Overview>("/api/stats/overview"),
  timeseries: (metric: string, interval = "hour", range = "24h") =>
    request<Timeseries>(`/api/stats/timeseries${qs({ metric, interval, range })}`),

  triggerDiscovery: () => request<{ discovered: number; new_devices: number }>("/api/scans/discovery", { method: "POST" }),
  triggerPortscan: (deviceId: number) =>
    request<{ open_ports: PortResult[] }>(`/api/scans/portscan/${deviceId}`, { method: "POST" }),
};

function qs(params?: Record<string, unknown>): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  if (!entries.length) return "";
  return "?" + new URLSearchParams(entries as [string, string][]).toString();
}

export { ApiError };

export interface Device {
  id: number;
  mac_address: string;
  vendor_oui: string | null;
  custom_name: string | null;
  hostname: string | null;
  is_known: boolean;
  first_seen: string;
  last_seen: string;
  current_ip: string | null;
  is_online: boolean;
}

export interface Sighting {
  id: number;
  ip_address: string;
  ssid: string | null;
  method: string;
  seen_at: string;
}

export interface DevicePort {
  id: number;
  port: number;
  proto: string;
  service_guess: string | null;
  first_seen: string;
  last_seen: string;
}

export interface PortResult {
  port: number;
  proto: string;
  service_guess: string | null;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Alert {
  id: number;
  ts: string;
  rule_key: string;
  severity: Severity;
  title: string;
  description: string;
  related_device_id: number | null;
  related_ip: string | null;
  source: string;
  status: "new" | "ack" | "resolved";
}

export interface AlertStats {
  total: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
}

export interface SuricataEvent {
  id: number;
  ts: string;
  event_type: string;
  severity: number | null;
  signature: string | null;
  category: string | null;
  src_ip: string | null;
  src_port: number | null;
  dst_ip: string | null;
  dst_port: number | null;
  proto: string | null;
}

export interface Connection {
  id: number;
  ts: string;
  src_ip: string;
  src_port: number | null;
  dst_ip: string;
  dst_port: number | null;
  proto: string;
  app_proto: string | null;
  bytes_in: number;
  bytes_out: number;
  packets: number;
  duration_ms: number;
}

export interface ConnectionStats {
  total_bytes: number;
  top_talkers: { ip: string; bytes: number }[];
  protocols: Record<string, number>;
}

export interface Overview {
  total_devices: number;
  online_devices: number;
  new_alerts: number;
  high_severity_alerts: number;
  events_24h: number;
  connections_24h: number;
}

export interface Timeseries {
  metric: string;
  interval: string;
  points: { t: string; v: number }[];
}
