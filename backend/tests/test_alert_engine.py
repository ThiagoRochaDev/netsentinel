import pytest

from app.alert_engine.engine import raise_alert, seed_static_advisories
from app.db import get_session
from app.models.alert import Alert


@pytest.mark.asyncio
async def test_raise_alert_persists_row():
    await raise_alert(
        rule_key="test_rule",
        severity="high",
        title="Título de teste",
        description="Descrição de teste",
        source="test",
        related_ip="192.168.1.10",
    )

    with get_session() as session:
        alert = session.query(Alert).filter(Alert.rule_key == "test_rule").first()

    assert alert is not None
    assert alert.severity == "high"
    assert alert.title == "Título de teste"
    assert alert.related_ip == "192.168.1.10"
    assert alert.status == "new"  # default do model


def test_seed_static_advisories_is_idempotent():
    seed_static_advisories()
    seed_static_advisories()  # chamar duas vezes não deve duplicar

    with get_session() as session:
        count = (
            session.query(Alert)
            .filter(Alert.rule_key == "default_router_credentials_reminder")
            .count()
        )

    assert count == 1
