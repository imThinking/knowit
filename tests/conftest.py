"""Test configuration and fixtures"""

import pytest
import tempfile
import shutil
from pathlib import Path

from kv.core.config import config
from kv.core.database import Base
from kv.services.database import DatabaseService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_vault.db"

    # Create test database
    test_engine = Base.metadata.create_all(engine)

    # Initialize database service with test database
    original_db_path = Config().home_dir / "data" / "vault.db"

    yield DatabaseService(db_path=str(db_path))

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_config():
    """Create a temporary config file for testing"""
    import tempfile
    from kv.services.config_service import ConfigService

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_file = Path(f.name)

    config = ConfigService(config_dir=temp_file.parent)
    config.config_file = temp_file

    yield config

    # Cleanup
    temp_file.unlink(missing_ok=True)
