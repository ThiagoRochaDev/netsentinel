from textual.app import ComposeResult
from textual.containers import Grid
from textual.widgets import Static


class StatTile(Static):
    def __init__(self, label: str, value: str = "--"):
        super().__init__()
        self.label = label
        self.value = value

    def render(self) -> str:
        return f"[bold]{self.value}[/bold]\n{self.label}"


class OverviewScreen(Grid):
    def __init__(self, api_client):
        super().__init__(id="overview-grid")
        self.api_client = api_client
        self.tiles = {
            "total_devices": StatTile("Dispositivos conhecidos"),
            "online_devices": StatTile("Online agora"),
            "new_alerts": StatTile("Alertas novos"),
            "high_severity_alerts": StatTile("Alertas graves"),
            "events_24h": StatTile("Eventos Suricata (24h)"),
            "connections_24h": StatTile("Conexões deste host (24h)"),
        }

    def compose(self) -> ComposeResult:
        for tile in self.tiles.values():
            yield tile

    def fetch(self):
        try:
            return self.api_client.get_overview()
        except Exception:
            return None

    def apply(self, data) -> None:
        if not data:
            return
        for key, tile in self.tiles.items():
            if key in data:
                tile.value = str(data[key])
                tile.refresh()
