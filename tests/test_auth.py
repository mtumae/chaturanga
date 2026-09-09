import pytest
from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.config import get_settings
from app.main import app

def _fake_auth() -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        payload={"sub": "user_fake123", "sid": "sess_fake"},
    )

@pytest.fixture(autouse=True)
def _override_auth():
    app.dependency_overrides[require_auth] = _fake_auth
    yield
    app.dependency_overrides = {}

def test_me_endpoint():
    client = TestClient(app)
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json() == {"user_id": "user_fake123", "session_id": "sess_fake"}

def test_unauthenticated_returns_401():
    app.dependency_overrides = {}
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/api/me")
    assert response.status_code == 401
