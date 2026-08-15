import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { LoginPage } from "./auth/LoginPage";
import { Layout } from "./components/Layout";
import { Alerts } from "./pages/Alerts";
import { Devices } from "./pages/Devices";
import { LogsExplorer } from "./pages/LogsExplorer";
import { Overview } from "./pages/Overview";
import { Traffic } from "./pages/Traffic";

function RequireAuth({ children }: { children: ReactElement }) {
  const { username, loading } = useAuth();
  if (loading) return null;
  if (!username) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { username } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={username ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Overview />} />
        <Route path="devices" element={<Devices />} />
        <Route path="traffic" element={<Traffic />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="logs" element={<LogsExplorer />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
