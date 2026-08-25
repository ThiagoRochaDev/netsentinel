"""Testa o router de alertas isoladamente (não usa app.main.app, que dispara
coletores de rede reais no lifespan — indesejável em CI)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.alert_engine.engine import raise_alert
from app.api.alerts import router as alerts_router
from app.auth.deps import get_current_username


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(alerts_router)
    app.dependency_overrides[get_current_username] = lambda: "test-user"
    return TestClient(app)


def test_health_endpoint():
    from app.main import health

    assert health() == {"status": "ok"}


def test_list_alerts_requires_auth_by_default():
    app = FastAPI()
    app.include_router(alerts_router)
    client = TestClient(app)

    response = client.get("/api/alerts")

    assert response.status_code == 401


async def _seed_one_alert():
    await raise_alert(
        rule_key="test_rule",
        severity="medium",
        title="Alerta de teste",
        description="desc",
        source="test",
    )


def test_list_alerts_returns_seeded_alert():
    import asyncio

    asyncio.run(_seed_one_alert())
    client = _make_client()

    response = client.get("/api/alerts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["rule_key"] == "test_rule"
    assert body[0]["status"] == "new"


def test_patch_alert_updates_status():
    import asyncio

    asyncio.run(_seed_one_alert())
    client = _make_client()
    alert_id = client.get("/api/alerts").json()[0]["id"]

    response = client.patch(f"/api/alerts/{alert_id}", json={"status": "ack"})

    assert response.status_code == 200
    assert response.json()["status"] == "ack"


def test_patch_alert_rejects_invalid_status():
    import asyncio

    asyncio.run(_seed_one_alert())
    client = _make_client()
    alert_id = client.get("/api/alerts").json()[0]["id"]

    response = client.patch(f"/api/alerts/{alert_id}", json={"status": "bogus"})

    assert response.status_code == 400
