import getpass
import os
from pathlib import Path

import httpx

_CONFIG_DIR = Path.home() / ".config" / "netsentinel"
_TOKEN_FILE = _CONFIG_DIR / "tui_session_cookie"


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._cookie: str | None = None
        self._client = httpx.Client(base_url=self.base_url, timeout=10.0)
        self._load_cookie()

    def _load_cookie(self) -> None:
        if _TOKEN_FILE.exists():
            self._cookie = _TOKEN_FILE.read_text().strip() or None
            if self._cookie:
                self._client.cookies.set("netsentinel_session", self._cookie)

    def _save_cookie(self, cookie: str) -> None:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _TOKEN_FILE.write_text(cookie)
        os.chmod(_TOKEN_FILE, 0o600)

    def is_authenticated(self) -> bool:
        if not self._cookie:
            return False
        try:
            resp = self._client.get("/api/auth/me")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def interactive_login(self) -> bool:
        print(f"NetSentinel TUI — login ({self.base_url})")
        username = input("Usuário: ")
        password = getpass.getpass("Senha: ")
        resp = self._client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        if resp.status_code != 200:
            print("Login falhou.")
            return False
        cookie = self._client.cookies.get("netsentinel_session")
        if cookie:
            self._save_cookie(cookie)
        return True

    def get_devices(self) -> list[dict]:
        resp = self._client.get("/api/devices")
        resp.raise_for_status()
        return resp.json()

    def get_alerts(self, status: str | None = None) -> list[dict]:
        params = {"status": status} if status else {}
        resp = self._client.get("/api/alerts", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_events(self, limit: int = 100) -> list[dict]:
        resp = self._client.get("/api/events", params={"limit": limit})
        resp.raise_for_status()
        return resp.json()

    def get_overview(self) -> dict:
        resp = self._client.get("/api/stats/overview")
        resp.raise_for_status()
        return resp.json()

    def ws_url(self) -> str:
        return self.base_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/ws/live"

    def cookie_header(self) -> str:
        return f"netsentinel_session={self._cookie}" if self._cookie else ""
