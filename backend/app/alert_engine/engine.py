import logging

from app.db import get_session, get_write_session
from app.models.alert import Alert
from app.ws_manager import ws_manager

logger = logging.getLogger("netsentinel.alert_engine")


def seed_static_advisories() -> None:
    """One-time advisories that don't depend on live collectors. Written
    directly (not via raise_alert) since this runs at startup before the
    WebSocket has any listeners, and should only ever be inserted once."""
    rule_key = "default_router_credentials_reminder"
    with get_session() as session:
        exists = session.query(Alert).filter(Alert.rule_key == rule_key).first()
    if exists:
        return

    with get_write_session() as session:
        session.add(
            Alert(
                rule_key=rule_key,
                severity="high",
                title="Roteador com credenciais padrão/fracas",
                description=(
                    "Você indicou que pelo menos um dos seus roteadores está usando "
                    "usuário/senha padrão de fábrica (admin/admin). Isso permite que "
                    "qualquer dispositivo na rede local — ou até de fora, se a "
                    "administração remota estiver ligada — assuma o controle total "
                    "do roteador. Troque a senha assim que possível pelo painel "
                    "administrativo do roteador."
                ),
                source="system",
            )
        )


async def raise_alert(
    rule_key: str,
    severity: str,
    title: str,
    description: str,
    source: str,
    related_device_id: int | None = None,
    related_ip: str | None = None,
    raw_ref: str | None = None,
) -> None:
    with get_write_session() as session:
        alert = Alert(
            rule_key=rule_key,
            severity=severity,
            title=title,
            description=description,
            source=source,
            related_device_id=related_device_id,
            related_ip=related_ip,
            raw_ref=raw_ref,
        )
        session.add(alert)
        session.flush()
        alert_id = alert.id

    logger.info("ALERT [%s] %s: %s", severity, rule_key, title)
    await ws_manager.broadcast(
        "new_alert",
        {
            "id": alert_id,
            "rule_key": rule_key,
            "severity": severity,
            "title": title,
            "description": description,
        },
    )
