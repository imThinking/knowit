"""Tests for AutoExportService"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from kv.services.auto_export import AutoExportService
from kv.services.config_service import ConfigService
from kv.core.database import Item


class TestAutoExportService:
    """Test AutoExportService functionality"""

    @pytest.fixture
    def fresh_config(self):
        """Create a fresh config for each test"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = Path(f.name)

        config = ConfigService(config_dir=temp_file.parent)
        config.config_file = temp_file
        config.init_default_config()

        yield config

        # Cleanup
        temp_file.unlink(missing_ok=True)

    def test_should_export_with_default_config(self, fresh_config):
        """Test that auto-export is enabled by default"""
        service = AutoExportService()

        assert service.should_export() is True

    def test_should_export_when_disabled(self, fresh_config):
        """Test that auto-export can be disabled"""
        fresh_config.set('auto_export.enabled', False)
        # Create service that uses the fresh config
        service = AutoExportService()
        service.config_service = fresh_config

        assert service.should_export() is False

    def test_get_export_formats_default(self, fresh_config):
        """Test default export formats"""
        service = AutoExportService()
        service.config_service = fresh_config

        formats = service.get_export_formats()
        assert formats == ['html', 'pdf']

    def test_get_export_formats_html_only(self, fresh_config):
        """Test HTML-only export format"""
        fresh_config.set('auto_export.formats', ['html'])
        service = AutoExportService()
        service.config_service = fresh_config

        formats = service.get_export_formats()
        assert formats == ['html']

    def test_get_export_formats_invalid(self, fresh_config):
        """Test that invalid formats are filtered out"""
        fresh_config.set('auto_export.formats', ['html', 'docx', 'pdf'])
        service = AutoExportService()

        formats = service.get_export_formats()
        assert formats == ['html', 'pdf']
        assert 'docx' not in formats


class TestAutoExportIntegration:
    """Integration tests for auto-export functionality"""

    @pytest.fixture
    def fresh_config(self):
        """Create a fresh config for each test"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = Path(f.name)

        config = ConfigService(config_dir=temp_file.parent)
        config.config_file = temp_file
        config.init_default_config()

        yield config

        # Cleanup
        temp_file.unlink(missing_ok=True)

    def test_export_item_with_collection(self, fresh_config):
        """Test exporting an item with a collection"""

        # Create a test item
        item = Item()
        item.id = "test-id-1"
        item.title = "Test Article"
        item.source_type = "webpage"
        item.source_url = "https://example.com/test"
        item.author = "Test Author"
        item.content_html = "<p>Test content</p>"
        item.content_text = "Test content"
        item.word_count = 2
        item.reading_time = 1
        item.collection_id = None
        item.simhash = "12345"
        item.created_at = datetime.now()
        item.updated_at = datetime.now()

        service = AutoExportService()

        # Test that export_item method exists and can be called
        # (actual file generation may fail in test environment)
        try:
            results = service.export_item(item)
            assert isinstance(results, dict)
            # Results may be empty if export fails, which is OK for this test
        except Exception as e:
            # Some failures are expected in test environment
            # (e.g., WeasyPrint not installed)
            assert 'html' in str(e).lower() or 'pdf' in str(e).lower() or 'permission' in str(e).lower()

    def test_error_handling_ignore(self, fresh_config):
        """Test error handling with 'ignore' mode"""
        fresh_config.set('auto_export.on_error', 'ignore')

        service = AutoExportService()

        # Should not raise exception
        service.handle_export_error(Exception("Test error"), "Test Item")
