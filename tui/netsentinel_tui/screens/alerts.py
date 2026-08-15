from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable

_SEVERITY_STYLE = {
    "critical": "bold white on red",
    "high": "bold red",
    "medium": "bold yellow",
    "low": "cyan",
    "info": "dim",
}


class AlertsScreen(Vertical):
    def __init__(self, api_client):
        super().__init__(id="alerts-screen")
        self.api_client = api_client

    def compose(self) -> ComposeResult:
        table = DataTable(id="alerts-table")
        table.cursor_type = "row"
        table.add_columns("Quando", "Severidade", "Regra", "Título", "Status")
        yield table

    def fetch(self):
        try:
            return self.api_client.get_alerts()
        except Exception:
            return None

    def apply(self, alerts) -> None:
        if alerts is None:
            return
        table = self.query_one("#alerts-table", DataTable)
        table.clear()
        for a in alerts:
            severity = a.get("severity", "info")
            style = _SEVERITY_STYLE.get(severity, "")
            table.add_row(
                (a.get("ts") or "")[:19].replace("T", " "),
                f"[{style}]{severity.upper()}[/]" if style else severity,
                a.get("rule_key", ""),
                a.get("title", ""),
                a.get("status", ""),
            )
