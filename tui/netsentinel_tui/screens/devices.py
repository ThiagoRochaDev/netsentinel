from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable


class DevicesScreen(Vertical):
    def __init__(self, api_client):
        super().__init__(id="devices-screen")
        self.api_client = api_client

    def compose(self) -> ComposeResult:
        table = DataTable(id="devices-table")
        table.cursor_type = "row"
        table.add_columns("MAC", "IP atual", "Fabricante", "Nome", "Hostname", "Visto por último")
        yield table

    def fetch(self):
        try:
            return self.api_client.get_devices()
        except Exception:
            return None

    def apply(self, devices) -> None:
        if devices is None:
            return
        table = self.query_one("#devices-table", DataTable)
        table.clear()
        for d in devices:
            table.add_row(
                d.get("mac_address", ""),
                d.get("current_ip") or "-",
                d.get("vendor_oui") or "-",
                d.get("custom_name") or "-",
                d.get("hostname") or "-",
                (d.get("last_seen") or "")[:19].replace("T", " "),
            )
