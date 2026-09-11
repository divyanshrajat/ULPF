"""
T6 acceptance test: health check must report actual component status,
not hardcoded 'healthy' strings.
"""
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_redis_down():
    """When Redis is unreachable, its component must show 'down' and overall 'degraded'."""
    with patch("app.main.redis_lib") as mock_redis_mod:
        mock_client = MagicMock()
        mock_client.ping.side_effect = ConnectionError("Connection refused")
        mock_redis_mod.Redis.from_url.return_value = mock_client

        resp = client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["redis"] == "down"
        assert data["status"] == "degraded"


def test_health_all_up():
    """When all components respond, overall must be 'healthy'."""
    with patch("app.main.redis_lib") as mock_redis_mod, \
         patch("app.main.get_opensearch_client") as mock_os_fn:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_mod.Redis.from_url.return_value = mock_client

        mock_os_client = MagicMock()
        mock_os_client.ping.return_value = True
        mock_os_fn.return_value = mock_os_client

        resp = client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["redis"] == "healthy"
        assert data["components"]["opensearch"] == "healthy"
        assert data["components"]["postgres"] == "healthy"
        assert data["status"] == "healthy"
