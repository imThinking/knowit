"""Full-text search service using Meilisearch

Provides document indexing and search functionality with Meilisearch.
Falls back to SQLite LIKE queries when Meilisearch is unavailable.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    import meilisearch
    MEILISEARCH_AVAILABLE = True
except ImportError:
    MEILISEARCH_AVAILABLE = False

from kv.core.config import config
from kv.core.exceptions import (
    SearchError,
    MeilisearchConnectionError,
    MeilisearchIndexError,
)
from kv.core.database import Item


logger = logging.getLogger(__name__)


class SearchResult:
    """Container for search results with metadata

    Attributes:
        item: The Item object
        score: Relevance score (0-1)
        highlighted_title: Title with search terms highlighted
        highlighted_content: Content excerpt with search terms highlighted
    """

    def __init__(
        self,
        item: Item,
        score: float = 0.0,
        highlighted_title: str = "",
        highlighted_content: str = "",
    ):
        self.item = item
        self.score = score
        self.highlighted_title = highlighted_title or item.title
        self.highlighted_content = highlighted_content or (item.content_text or "")[:300]


class MeilisearchService:
    """Meilisearch client for KnowIt

    Handles document indexing, searching, and management.
    Automatically falls back to SQLite when unavailable.

    Attributes:
        client: Meilisearch client instance (None if unavailable)
        index_name: Name of the search index
        enabled: Whether Meilisearch is available and connected
    """

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize Meilisearch client

        Args:
            url: Meilisearch server URL (from config if None)
            api_key: Optional API key (from config if None)
        """
        if not MEILISEARCH_AVAILABLE:
            self.client = None
            self.enabled = False
            logger.warning("Meilisearch Python package not installed. Install with: pip install meilisearch")
            return

        self.index_name = "items"
        url = url or config.meilisearch_url

        try:
            self.client = meilisearch.Client(url=url, api_key=api_key)
            # Test connection
            self.client.health()
            self.enabled = True
            logger.info(f"Connected to Meilisearch at {url}")
        except Exception as e:
            self.client = None
            self.enabled = False
            logger.warning(f"Failed to connect to Meilisearch: {e}")

    def create_index(self) -> None:
        """Create the search index with settings

        Raises:
            MeilisearchConnectionError: If not connected
            MeilisearchIndexError: If index creation fails
        """
        if not self.enabled or not self.client:
            raise MeilisearchConnectionError(config.meilisearch_url, "Not connected")

        try:
            # Create index if it doesn't exist
            try:
                self.client.create_index(
                    self.index_name,
                    {"primaryKey": "id"}
                )
            except meilisearch.errors.MeilisearchApiError as e:
                # Index might already exist
                if "already_exists" not in str(e):
                    raise MeilisearchIndexError(self.index_name, str(e))

            # Configure searchable fields and ranking
            index = self.client.index(self.index_name)

            # Update searchable attributes
            index.update_searchable_attributes([
                "title",
                "content_text",
                "tags",
                "author"
            ])

            # Configure ranking rules
            index.update_ranking_rules([
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness"
            ])

            # Configure displayed attributes
            index.update_displayed_attributes([
                "id",
                "title",
                "content_text",
                "author",
                "tags",
                "source_type",
                "source_url",
                "created_at",
                "collection_id"
            ])

            # Configure filterable attributes
            index.update_filterable_attributes([
                "status",
                "source_type",
                "collection_id",
                "created_at"
            ])

            logger.info(f"Meilisearch index '{self.index_name}' configured")
        except Exception as e:
            raise MeilisearchIndexError(self.index_name, str(e))

    def index_item(self, item: Item) -> None:
        """Add or update an item in the search index

        Args:
            item: Item to index

        Raises:
            MeilisearchIndexError: If indexing fails
        """
        if not self.enabled or not self.client:
            return

        try:
            # Prepare document
            document = {
                "id": item.id,
                "title": item.title,
                "content_text": item.content_text or "",
                "author": item.author or "",
                "tags": [],  # Would need to fetch tags separately
                "source_type": item.source_type,
                "source_url": item.source_url or "",
                "status": item.status,
                "collection_id": item.collection_id or "",
                "created_at": item.created_at.isoformat() if item.created_at else "",
            }

            # Add to index
            index = self.client.index(self.index_name)
            index.update_documents([document])

            logger.debug(f"Indexed item {item.id}")
        except Exception as e:
            logger.error(f"Failed to index item {item.id}: {e}")
            raise MeilisearchIndexError(self.index_name, str(e))

    def remove_item(self, item_id: str) -> None:
        """Remove an item from the search index

        Args:
            item_id: Item UUID to remove
        """
        if not self.enabled or not self.client:
            return

        try:
            index = self.client.index(self.index_name)
            index.delete_document(item_id)
            logger.debug(f"Removed item {item_id} from index")
        except Exception as e:
            logger.error(f"Failed to remove item {item_id} from index: {e}")

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search for items

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            filters: Optional Meilisearch filter expression

        Returns:
            List of SearchResult objects

        Raises:
            MeilisearchIndexError: If search fails
        """
        if not self.enabled or not self.client:
            return []

        try:
            index = self.client.index(self.index_name)

            search_params: Dict[str, Any] = {
                "limit": limit,
                "offset": offset,
                "attributesToHighlight": ["title", "content_text"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
            }

            if filters:
                search_params["filter"] = filters

            results = index.search(query, search_params)

            # Convert to SearchResult objects
            search_results = []
            for hit in results.get("hits", []):
                # Get formatted result with highlights
                formatted = hit.get("_formatted", {})

                search_results.append(
                    SearchResult(
                        item=Item(
                            id=hit["id"],
                            title=hit["title"],
                            content_text=hit.get("content_text", ""),
                            author=hit.get("author"),
                            source_type=hit.get("source_type", ""),
                            source_url=hit.get("source_url"),
                            created_at=datetime.fromisoformat(hit["created_at"]) if hit.get("created_at") else None,
                        ),
                        score=hit.get("_rankingScore", 0.0),
                        highlighted_title=formatted.get("title", ""),
                        highlighted_content=formatted.get("content_text", ""),
                    )
                )

            return search_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise MeilisearchIndexError(self.index_name, str(e))

    def delete_index(self) -> None:
        """Delete the entire search index

        Use with caution! This requires reindexing all items.
        """
        if not self.enabled or not self.client:
            return

        try:
            self.client.delete_index(self.index_name)
            logger.info(f"Deleted Meilisearch index '{self.index_name}'")
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            raise MeilisearchIndexError(self.index_name, str(e))

    def get_index_stats(self) -> Optional[Dict[str, Any]]:
        """Get index statistics

        Returns:
            Dict with stats like number of documents, field distribution, etc.
            Returns None if Meilisearch is unavailable.
        """
        if not self.enabled or not self.client:
            return None

        try:
            index = self.client.index(self.index_name)
            return index.get_stats()
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return None


# Global search service instance
search_service = MeilisearchService()
