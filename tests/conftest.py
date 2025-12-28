"""
Pytest configuration and fixtures
"""
import pytest
import pytest_asyncio
from hypothesis import settings, HealthCheck

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Configure Hypothesis globally to suppress health checks
settings.register_profile(
    "default",
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.filter_too_much,
    ],
    deadline=10000,  # 10 seconds for slow tests with retries
)
settings.load_profile("default")

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
