"""Tests for search service"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kv.services.search_service import MeilisearchService, SearchResult
from kv.core.database import Item
from datetime import datetime


# Mock meilisearch module
mock_meilisearch = MagicMock()
sys = MagicMock()
sys.modules['meilisearch'] = mock_meilisearch
sys.modules['meilisearch.errors'] = MagicMock()


class TestMeilisearchService:
    """Test Meilisearch service"""

    def test_init_without_meilisearch(self):
        """Test initialization when Meilisearch is not available"""
        with patch('kv.services.search_service.MEILISEARCH_AVAILABLE', False):
            service = MeilisearchService()

            assert service.enabled is False
            assert service.client is None

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_init_with_meilisearch_success(self, mock_meilisearch):
        """Test successful Meilisearch connection"""
        mock_client = Mock()
        mock_client.health.return_value = True
        mock_meilisearch.Client.return_value = mock_client

        service = MeilisearchService()

        assert service.enabled is True
        assert service.client is not None

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_init_connection_failure(self, mock_meilisearch):
        """Test handling connection failure"""
        mock_client = Mock()
        mock_client.health.side_effect = Exception("Connection failed")
        mock_meilisearch.Client.return_value = mock_client

        service = MeilisearchService()

        assert service.enabled is False
        assert service.client is None

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_create_index(self, mock_meilisearch):
        """Test creating search index"""
        mock_client = Mock()
        mock_client.health.return_value = True
        mock_client.create_index.return_value = True

        mock_index = Mock()
        mock_client.index.return_value = mock_index

        mock_meilisearch.Client.return_value = mock_client
        mock_meilisearch.errors.MeilisearchApiError = Exception

        service = MeilisearchService()
        service.create_index()

        # Verify index methods were called
        assert mock_index.update_searchable_attributes.called
        assert mock_index.update_filterable_attributes.called

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_index_item(self, mock_meilisearch, sample_item):
        """Test indexing an item"""
        mock_client = Mock()
        mock_client.health.return_value = True

        mock_index = Mock()
        mock_client.index.return_value = mock_index

        mock_meilisearch.Client.return_value = mock_client

        service = MeilisearchService()
        service.index_item(sample_item)

        # Verify document was added
        mock_index.update_documents.assert_called_once()

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_search(self, mock_meilisearch):
        """Test searching items"""
        mock_client = Mock()
        mock_client.health.return_value = True

        mock_index = Mock()
        mock_index.search.return_value = {
            'hits': [
                {
                    'id': 'test-id',
                    'title': 'Test Article',
                    'content_text': 'Test content',
                    'author': 'Test Author',
                    'source_type': 'webpage',
                    'source_url': 'https://example.com',
                    'created_at': datetime.now().isoformat(),
                    '_formatted': {
                        'title': '<mark>Test</mark> Article',
                        'content_text': '<mark>Test</mark> content'
                    },
                    '_rankingScore': 0.95
                }
            ],
            'estimatedTotalHits': 1
        }
        mock_client.index.return_value = mock_index

        mock_meilisearch.Client.return_value = mock_client

        service = MeilisearchService()
        results = service.search("test query")

        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].item.title == "Test Article"
        assert results[0].score > 0

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_search_with_filters(self, mock_meilisearch):
        """Test searching with filters"""
        mock_client = Mock()
        mock_client.health.return_value = True

        mock_index = Mock()
        mock_index.search.return_value = {'hits': [], 'estimatedTotalHits': 0}
        mock_client.index.return_value = mock_index

        mock_meilisearch.Client.return_value = mock_client

        service = MeilisearchService()
        service.search("test", filters="status = inbox")

        # Verify filter was passed
        mock_index.search.assert_called_once()
        call_kwargs = mock_index.search.call_args[1]
        assert 'filter' in call_kwargs

    @patch('kv.services.search_service.MEILISEARCH_AVAILABLE', True)
    @patch('kv.services.search_service.meilisearch')
    def test_get_index_stats(self, mock_meilisearch):
        """Test getting index statistics"""
        mock_client = Mock()
        mock_client.health.return_value = True

        mock_index = Mock()
        mock_index.get_stats.return_value = {
            'numberOfDocuments': 100,
            'fieldDistribution': {'title': 100, 'content_text': 100}
        }
        mock_client.index.return_value = mock_index

        mock_meilisearch.Client.return_value = mock_client

        service = MeilisearchService()
        stats = service.get_index_stats()

        assert stats is not None
        assert stats['numberOfDocuments'] == 100


class TestSearchResult:
    """Test SearchResult class"""

    def test_init(self):
        """Test SearchResult initialization"""
        item = Item(
            id="test-id",
            title="Test Article",
            source_type="webpage",
            status="inbox"
        )

        result = SearchResult(
            item=item,
            score=0.95,
            highlighted_title="<mark>Test</mark> Article",
            highlighted_content="<mark>Test</mark> content"
        )

        assert result.item.id == "test-id"
        assert result.score == 0.95
        assert result.highlighted_title == "<mark>Test</mark> Article"
        assert "mark" in result.highlighted_content

    def test_defaults(self):
        """Test SearchResult with default values"""
        item = Item(
            id="test-id",
            title="Test",
            source_type="webpage",
            content_text="Test content",
            status="inbox"
        )

        result = SearchResult(item=item)

        assert result.score == 0.0
        assert result.highlighted_title == "Test"
        assert result.highlighted_content == "Test content"
