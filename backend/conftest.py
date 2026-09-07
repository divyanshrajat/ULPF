import pytest
import psycopg2
from app.core.config import settings

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "postgres: mark test to run only if postgres is available"
    )

def is_postgres_available():
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname=settings.POSTGRES_DB,
            connect_timeout=1
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

@pytest.fixture(autouse=True)
def check_postgres_marker(request):
    marker = request.node.get_closest_marker("postgres")
    if marker:
        if not is_postgres_available():
            if "postgres" in request.config.getoption("markexpr"):
                pytest.fail("PostgreSQL infrastructure is unavailable but explicitly requested via -m postgres")
            else:
                pytest.skip("PostgreSQL infrastructure is unavailable")
