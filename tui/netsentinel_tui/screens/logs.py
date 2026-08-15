from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Input


class LogsScreen(Vertical):
    def __init__(self, api_client):
        super().__init__(id="logs-screen")
        self.api_client = api_client
        self._search = ""

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Buscar (IP, assinatura)...", id="logs-search")
        table = DataTable(id="logs-table")
        table.cursor_type = "row"
        table.add_columns("Quando", "Tipo", "Severidade", "Assinatura", "Origem", "Destino", "Proto")
        yield table

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "logs-search":
            self._search = event.value
            data = self.fetch()
            self.apply(data)

    def fetch(self):
        try:
            return self.api_client.get_events(limit=200)
        except Exception:
            return None

    def apply(self, events) -> None:
        if events is None:
            return
        table = self.query_one("#logs-table", DataTable)
        table.clear()
        for e in events:
            if self._search and self._search.lower() not in str(e).lower():
                continue
            table.add_row(
                (e.get("ts") or "")[:19].replace("T", " "),
                e.get("event_type", ""),
                str(e.get("severity") or "-"),
                e.get("signature") or "-",
                f"{e.get('src_ip') or '-'}:{e.get('src_port') or ''}",
                f"{e.get('dst_ip') or '-'}:{e.get('dst_port') or ''}",
                e.get("proto") or "-",
            )
