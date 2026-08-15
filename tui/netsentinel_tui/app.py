import os

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane

from netsentinel_tui.api_client import ApiClient
from netsentinel_tui.screens.alerts import AlertsScreen
from netsentinel_tui.screens.devices import DevicesScreen
from netsentinel_tui.screens.logs import LogsScreen
from netsentinel_tui.screens.overview import OverviewScreen

REFRESH_INTERVAL_SECONDS = 5

CSS = """
Screen {
    background: #0b0f14;
    color: #d6e2e6;
}
#overview-grid {
    grid-size: 3 2;
    grid-gutter: 1 2;
    padding: 1 2;
}
StatTile {
    background: #121820;
    border: round #223040;
    padding: 1 2;
    text-align: center;
    height: 5;
}
DataTable {
    background: #0b0f14;
}
Header, Footer {
    background: #121820;
}
"""


class NetSentinelApp(App):
    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Sair"),
        ("r", "manual_refresh", "Atualizar"),
    ]
    TITLE = "NetSentinel"
    SUB_TITLE = "Monitoramento da sua rede"

    def __init__(self):
        super().__init__()
        base_url = os.environ.get("NETSENTINEL_API_URL", "http://localhost:8000")
        self.api_client = ApiClient(base_url)

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Overview", id="tab-overview"):
                yield OverviewScreen(self.api_client)
            with TabPane("Dispositivos", id="tab-devices"):
                yield DevicesScreen(self.api_client)
            with TabPane("Alertas", id="tab-alerts"):
                yield AlertsScreen(self.api_client)
            with TabPane("Logs", id="tab-logs"):
                yield LogsScreen(self.api_client)
        yield Footer()

    def on_mount(self) -> None:
        # `run()` below already ensures a valid session before the app starts.
        self.action_manual_refresh()
        self.set_interval(REFRESH_INTERVAL_SECONDS, self.action_manual_refresh)

    def action_manual_refresh(self) -> None:
        self.run_worker(self._refresh_all, thread=True)

    def _refresh_all(self) -> None:
        # Runs in a worker thread: blocking HTTP fetches happen here, then
        # each screen's `apply()` (UI mutation) is marshalled back onto the
        # main thread via call_from_thread — Textual widgets aren't safe to
        # touch directly from a background thread.
        for screen in (
            self.query_one(OverviewScreen),
            self.query_one(DevicesScreen),
            self.query_one(AlertsScreen),
            self.query_one(LogsScreen),
        ):
            data = screen.fetch()
            self.call_from_thread(screen.apply, data)


def run() -> None:
    app = NetSentinelApp()
    if not app.api_client.is_authenticated():
        if not app.api_client.interactive_login():
            return
    app.run()
