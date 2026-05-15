"""Comprehensive tests for DatabaseService"""

import pytest
from datetime import datetime

from kv.services.database import DatabaseService
from kv.core.database import Item, Collection, Tag
from kv.core.exceptions import (
    ItemNotFoundError,
    DuplicateItemError,
    DuplicateCollectionError,
    DuplicateTagError,
    CollectionNotFoundError,
    TagNotFoundError,
)


class TestDatabaseServiceItems:
    """Test item-related database operations"""

    def test_create_item(self, temp_db):
        """Test creating a new item"""
        item = temp_db.create_item(
            title="Test Article",
            source_type="webpage",
            source_url="https://example.com/test",
        )

        assert item.id is not None
        assert item.title == "Test Article"
        assert item.source_type == "webpage"
        assert item.source_url == "https://example.com/test"
        assert item.status == "inbox"
        assert item.created_at is not None

    def test_get_item(self, temp_db, sample_item):
        """Test retrieving an item by ID"""
        retrieved = temp_db.get_item(sample_item.id)

        assert retrieved is not None
        assert retrieved.id == sample_item.id
        assert retrieved.title == sample_item.title

    def test_get_item_not_found(self, temp_db):
        """Test retrieving non-existent item"""
        result = temp_db.get_item("non-existent-id")
        assert result is None

    def test_get_items(self, temp_db):
        """Test retrieving multiple items"""
        # Create multiple items
        for i in range(5):
            temp_db.create_item(
                title=f"Item {i}",
                source_type="webpage",
            )

        items = temp_db.get_items(limit=10)

        assert len(items) >= 5
        assert all(isinstance(item, Item) for item in items)

    def test_get_items_with_filters(self, temp_db):
        """Test retrieving items with filters"""
        # Create items with different statuses
        item1 = temp_db.create_item(title="Inbox Item", source_type="webpage")
        temp_db.update_item(item1.id, status="inbox")

        item2 = temp_db.create_item(title="Archived Item", source_type="webpage")
        temp_db.update_item(item2.id, status="archived")

        inbox_items = temp_db.get_items(status="inbox")
        archived_items = temp_db.get_items(status="archived")

        assert all(item.status == "inbox" for item in inbox_items)
        assert all(item.status == "archived" for item in archived_items)

    def test_update_item(self, temp_db, sample_item):
        """Test updating an item"""
        updated = temp_db.update_item(
            sample_item.id,
            title="Updated Title",
            author="Updated Author"
        )

        assert updated.title == "Updated Title"
        assert updated.author == "Updated Author"

    def test_delete_item(self, temp_db, sample_item):
        """Test deleting an item"""
        result = temp_db.delete_item(sample_item.id)

        assert result is True

        # Verify item is deleted
        retrieved = temp_db.get_item(sample_item.id)
        assert retrieved is None

    def test_find_by_url(self, temp_db):
        """Test finding item by URL"""
        item = temp_db.create_item(
            title="Test",
            source_type="webpage",
            source_url="https://example.com/unique"
        )

        found = temp_db.find_by_url("https://example.com/unique")

        assert found is not None
        assert found.id == item.id

    def test_search_items(self, temp_db):
        """Test full-text search"""
        temp_db.create_item(
            title="Python Programming Guide",
            source_type="webpage",
            content_text="Learn Python programming from scratch"
        )
        temp_db.create_item(
            title="JavaScript Tutorial",
            source_type="webpage",
            content_text="Learn JavaScript basics"
        )

        results = temp_db.search_items("Python")

        assert len(results) > 0
        assert any("Python" in item.title for item in results)


class TestDatabaseServiceCollections:
    """Test collection-related database operations"""

    def test_create_collection(self, temp_db):
        """Test creating a collection"""
        collection = temp_db.create_collection(
            name="Python",
            description="Python programming articles"
        )

        assert collection.id is not None
        assert collection.name == "Python"
        assert collection.description == "Python programming articles"
        assert collection.item_count == 0

    def test_create_duplicate_collection(self, temp_db):
        """Test creating collection with duplicate name"""
        temp_db.create_collection(name="Python")

        with pytest.raises(DuplicateCollectionError):
            temp_db.create_collection(name="Python")

    def test_get_collections(self, temp_db):
        """Test retrieving all collections"""
        temp_db.create_collection(name="Python")
        temp_db.create_collection(name="JavaScript")

        collections = temp_db.get_collections()

        assert len(collections) >= 2
        collection_names = [c.name for c in collections]
        assert "Python" in collection_names
        assert "JavaScript" in collection_names

    def test_get_collection_by_name(self, temp_db):
        """Test retrieving collection by name"""
        temp_db.create_collection(name="Test Collection")

        collection = temp_db.get_collection_by_name("Test Collection")

        assert collection is not None
        assert collection.name == "Test Collection"

    def test_update_collection(self, temp_db, sample_collection):
        """Test updating a collection"""
        updated = temp_db.update_collection(
            sample_collection.id,
            description="Updated description"
        )

        assert updated.description == "Updated description"

    def test_delete_collection(self, temp_db, sample_collection):
        """Test deleting a collection"""
        result = temp_db.delete_collection(sample_collection.id)

        assert result is True

        # Verify collection is deleted
        retrieved = temp_db.get_collection(sample_collection.id)
        assert retrieved is None


class TestDatabaseServiceTags:
    """Test tag-related database operations"""

    def test_create_tag(self, temp_db):
        """Test creating a tag"""
        tag = temp_db.create_tag(name="python", color="#00FF00")

        assert tag.id is not None
        assert tag.name == "python"
        assert tag.color == "#00FF00"
        assert tag.use_count == 0

    def test_create_duplicate_tag(self, temp_db):
        """Test creating tag with duplicate name"""
        temp_db.create_tag(name="test")

        with pytest.raises(DuplicateTagError):
            temp_db.create_tag(name="test")

    def test_get_tags(self, temp_db):
        """Test retrieving all tags"""
        temp_db.create_tag(name="python")
        temp_db.create_tag(name="javascript")

        tags = temp_db.get_tags()

        assert len(tags) >= 2
        tag_names = [t.name for t in tags]
        assert "python" in tag_names
        assert "javascript" in tag_names

    def test_add_tag_to_item(self, temp_db, sample_item):
        """Test adding a tag to an item"""
        tag = temp_db.add_tag_to_item(sample_item.id, "test-tag")

        assert tag.name == "test-tag"
        assert tag.use_count >= 1

    def test_get_item_tags(self, temp_db, sample_item):
        """Test retrieving tags for an item"""
        temp_db.add_tag_to_item(sample_item.id, "tag1")
        temp_db.add_tag_to_item(sample_item.id, "tag2")

        tags = temp_db.get_item_tags(sample_item.id)

        assert len(tags) == 2
        tag_names = [t.name for t in tags]
        assert "tag1" in tag_names
        assert "tag2" in tag_names

    def test_remove_tag_from_item(self, temp_db, sample_item):
        """Test removing a tag from an item"""
        tag = temp_db.add_tag_to_item(sample_item.id, "test-tag")

        result = temp_db.remove_tag_from_item(sample_item.id, tag.id)

        assert result is True

        # Verify tag is removed
        tags = temp_db.get_item_tags(sample_item.id)
        assert tag not in tags


class TestDatabaseServiceSimilarity:
    """Test similarity-related database operations"""

    def test_save_similarity(self, temp_db):
        """Test saving similarity score"""
        item1 = temp_db.create_item(title="Item 1", source_type="webpage")
        item2 = temp_db.create_item(title="Item 2", source_type="webpage")

        similarity = temp_db.save_similarity(
            item1.id,
            item2.id,
            0.85,
            method="simhash"
        )

        assert similarity.item_id_1 in [item1.id, item2.id]
        assert similarity.item_id_2 in [item1.id, item2.id]
        assert similarity.similarity == 0.85
        assert similarity.method == "simhash"

    def test_get_similar_items(self, temp_db):
        """Test retrieving similar items"""
        item1 = temp_db.create_item(title="Item 1", source_type="webpage")
        item2 = temp_db.create_item(title="Item 2", source_type="webpage")

        temp_db.save_similarity(item1.id, item2.id, 0.85)

        similar = temp_db.get_similar_items(item1.id, threshold=0.75)

        assert len(similar) > 0
        assert item2.id in [item[0].id for item in similar]
