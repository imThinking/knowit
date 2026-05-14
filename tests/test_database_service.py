"""Tests for DatabaseService

Note: These are integration tests that require a working database.
For now, we'll test with the actual database service.
"""

import pytest


class TestDatabaseServiceIntegration:
    """Integration tests for DatabaseService"""

    def test_database_service_exists(self):
        """Test that database service can be imported and instantiated"""
        from kv.services.database import db

        assert db is not None
        assert hasattr(db, 'get_item')
        assert hasattr(db, 'create_item')
        assert hasattr(db, 'find_by_url')

    def test_get_collections(self):
        """Test getting collections from database"""
        from kv.services.database import db

        # This should not raise an exception
        collections = db.get_collections()
        assert isinstance(collections, list)

    def test_get_items(self):
        """Test getting items from database"""
        from kv.services.database import db

        # This should not raise an exception
        items = db.get_items(limit=5)
        assert isinstance(items, list)
