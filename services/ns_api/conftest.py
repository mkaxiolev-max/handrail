"""conftest.py — fixtures for ns_api integration tests against live service."""
import pytest
import httpx

NS_CORE_BASE = "http://localhost:9000"


@pytest.fixture
def client():
    """Async httpx client pointing at live ns_api (used with pytest-anyio / asyncio)."""
    return httpx.AsyncClient(base_url=NS_CORE_BASE, timeout=10.0)


@pytest.fixture
def chain():
    pytest.skip("chain fixture requires direct ns_api service internals")


@pytest.fixture
def canon_service():
    pytest.skip("canon_service fixture requires direct ns_api service internals")


@pytest.fixture
def voice_repo():
    pytest.skip("voice_repo fixture requires direct ns_api service internals")


@pytest.fixture
def alexandria_repo():
    pytest.skip("alexandria_repo fixture requires direct ns_api service internals")


@pytest.fixture
def db():
    pytest.skip("db fixture requires direct ns_api service internals")
