import socket
import pytest
from fastapi.testclient import TestClient

def test_airgap_startup(monkeypatch):
    """
    Ensure the application initializes and responds to health checks 
    without making any external network requests (e.g., to LLM APIs or 
    update servers).
    """
    original_connect = socket.socket.connect
    
    def mocked_connect(self, address):
        # address is usually a tuple of (host, port)
        if isinstance(address, tuple):
            host, port = address
            # Allow local connections for db, redis, opensearch
            if host not in ("127.0.0.1", "localhost", "::1", "postgres", "redis", "opensearch"):
                raise OSError(f"Network access blocked in airgap test: {host}:{port}")
        return original_connect(self, address)
        
    monkeypatch.setattr(socket.socket, "connect", mocked_connect)
    
    # Import app AFTER mocking to catch any on-load requests
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "2.0.0"}
