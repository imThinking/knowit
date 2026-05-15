"""Test configuration and fixtures

Provides pytest fixtures for testing KnowIt components.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from kv.core.database import Base, Item, Collection, Tag
from kv.services.database import DatabaseService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def temp_db(temp_dir):
    """Create a temporary database for testing

    Returns:
        DatabaseService instance with temporary database
    """
    db_path = temp_dir / "test_vault.db"

    # Create test database service with custom path
    test_db = DatabaseService()
    test_db.engine = create_engine(f"sqlite:///{db_path}")
    test_db.SessionLocal = sessionmaker(bind=test_db.engine, autoflush=False, autocommit=False)

    # Initialize tables
    test_db.init_db()

    yield test_db

    # Cleanup - Close all connections first
    test_db.engine.dispose()


@pytest.fixture
def sample_item(temp_db):
    """Create a sample item for testing

    Returns:
        Item object
    """
    item = temp_db.create_item(
        title="Test Article",
        source_type="webpage",
        source_url="https://example.com/test",
        author="Test Author",
        content_html="<p>Test content</p>",
        content_text="Test content",
        word_count=2,
        reading_time=1,
        simhash="abc123",
    )
    return item


@pytest.fixture
def sample_collection(temp_db):
    """Create a sample collection for testing

    Returns:
        Collection object
    """
    import uuid
    collection = temp_db.create_collection(
        name=f"Test Collection {uuid.uuid4().hex[:8]}",
        description="A test collection"
    )
    return collection


@pytest.fixture
def sample_tag(temp_db):
    """Create a sample tag for testing

    Returns:
        Tag object
    """
    import uuid
    tag = temp_db.create_tag(
        name=f"test-tag-{uuid.uuid4().hex[:8]}",
        color="#FF0000"
    )
    return tag


@pytest.fixture
def mock_scraper_response():
    """Mock scraper response for testing

    Returns:
        Mock ScrapedContent object
    """
    from kv.services.scraper import ScrapedContent

    return ScrapedContent(
        title="Mock Article Title",
        content_html="<div><p>Mock HTML content</p></div>",
        content_text="Mock HTML content",
        author="Mock Author",
        word_count=3,
        reading_time=1,
    )


@pytest.fixture
def mock_requests():
    """Mock requests module for testing"""
    with patch('requests.Session') as mock:
        session = Mock()
        mock.return_value = session
        yield session


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Article</title>
        <meta name="author" content="John Doe">
        <meta property="og:title" content="OG Title">
    </head>
    <body>
        <article>
            <h1>Main Heading</h1>
            <p>This is a sample paragraph with some text content.</p>
            <p>Another paragraph for testing word counting.</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def cli_runner():
    """Create Click CLI test runner"""
    from click.testing import CliRunner
    return CliRunner()


# Required imports for temp_db fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
