import { useEffect, useRef } from "react";

export type LiveMessage =
  | { type: "new_alert"; payload: { id: number; severity: string; title: string } }
  | { type: "new_device"; payload: { id: number; mac_address: string } }
  | { type: "suricata_event"; payload: Record<string, unknown> }
  | { type: "flow_tick"; payload: Record<string, unknown> };

export function useLiveSocket(onMessage: (msg: LiveMessage) => void) {
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let closedByUs = false;
    let retryDelay = 1000;

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      socket = new WebSocket(`${protocol}//${window.location.host}/api/ws/live`);

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as LiveMessage;
          handlerRef.current(msg);
        } catch {
          // ignore malformed frames
        }
      };

      socket.onclose = () => {
        if (closedByUs) return;
        setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 1.5, 15000);
      };
    }

    connect();
    return () => {
      closedByUs = true;
      socket?.close();
    };
  }, []);
}
