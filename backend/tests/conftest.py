import pytest
from app.core.database import init_db

@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure all database tables and seed baseline records are created before tests execute."""
    init_db()
