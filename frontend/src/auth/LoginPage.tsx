import { useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Falha ao conectar com o backend.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100dvh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--surface-0)",
        padding: 16,
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="card"
        style={{
          width: 340,
          maxWidth: "100%",
          padding: 32,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.01em" }}>NetSentinel</div>
          <div className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>
            Monitoramento de segurança — sua rede
          </div>
        </div>

        <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 13 }} className="text-secondary">
          Usuário
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
        </label>

        <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 13 }} className="text-secondary">
          Senha
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>

        {error && (
          <div style={{ color: "var(--status-critical)", fontSize: 13 }} role="alert">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          style={{
            background: "var(--series-1)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius-sm)",
            padding: "10px 16px",
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {submitting ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
