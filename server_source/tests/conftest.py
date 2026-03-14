# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
import pytest

from storage.sqlite_db import reset_conn, get_conn

# Force isolated in-memory DB for each test function
os.environ.setdefault("SQLITE_PATH", ":memory:")


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    # Reset connection (drops :memory: DB)
    reset_conn()
    # Ensure schema initialized
    get_conn()
    yield
    # Cleanup
    reset_conn()