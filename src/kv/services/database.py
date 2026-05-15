"""Database service layer for CRUD operations

Provides a high-level interface for managing knowledge items,
collections, tags, and their relationships.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from kv.core.config import config
from kv.core.database import Base, Item, Collection, Tag, ItemTag, ItemSimilarity
from kv.core.exceptions import (
    DatabaseError,
    ItemNotFoundError,
    CollectionNotFoundError,
    TagNotFoundError,
    DuplicateItemError,
    DuplicateCollectionError,
    DuplicateTagError,
)


class DatabaseService:
    """Database service for managing knowledge items

    Provides methods for CRUD operations on Items, Collections, Tags,
    and their relationships. Uses SQLAlchemy ORM with SQLite backend.

    Attributes:
        engine: SQLAlchemy engine
        SessionLocal: Session factory for creating new sessions
    """

    def __init__(self) -> None:
        """Initialize database service

        Creates engine and session factory from configuration.
        """
        self.engine = create_engine(f"sqlite:///{config.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def get_session(self) -> Session:
        """Get a new database session

        Returns:
            New SQLAlchemy session

        Note:
            Sessions should be used in context managers or properly closed.
        """
        return self.SessionLocal()

    def init_db(self) -> None:
        """Initialize database tables

        Creates all tables if they don't exist.
        Uses SQLAlchemy's create_all which is idempotent.
        """
        try:
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to initialize database: {e}")

    # ========== Item Operations ==========

    def create_item(
        self,
        title: str,
        source_type: str,
        source_url: Optional[str] = None,
        author: Optional[str] = None,
        content_html: Optional[str] = None,
        content_markdown: Optional[str] = None,
        content_text: Optional[str] = None,
        word_count: Optional[int] = None,
        reading_time: Optional[int] = None,
        collection_id: Optional[str] = None,
        simhash: Optional[str] = None,
    ) -> Item:
        """Create a new knowledge item

        Args:
            title: Item title
            source_type: Type of source ('webpage', 'wechat', 'local', 'manual')
            source_url: Optional source URL
            author: Optional author name
            content_html: Optional HTML content
            content_markdown: Optional Markdown content
            content_text: Optional plain text content
            word_count: Optional word count
            reading_time: Optional reading time in minutes
            collection_id: Optional collection ID to add item to
            simhash: Optional simhash for deduplication

        Returns:
            Created Item object

        Raises:
            DatabaseError: If item creation fails
        """
        try:
            with self.get_session() as session:
                item = Item(
                    id=str(uuid.uuid4()),
                    title=title,
                    source_type=source_type,
                    source_url=source_url,
                    author=author,
                    content_html=content_html,
                    content_markdown=content_markdown,
                    content_text=content_text,
                    word_count=word_count,
                    reading_time=reading_time,
                    collection_id=collection_id,
                    simhash=simhash,
                    status="inbox",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                return item
        except IntegrityError as e:
            raise DatabaseError(f"Failed to create item: {e}")

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID

        Args:
            item_id: Item UUID

        Returns:
            Item object or None if not found
        """
        with self.get_session() as session:
            return session.query(Item).filter(Item.id == item_id).first()

    def get_items(
        self,
        status: Optional[str] = None,
        collection_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Item]:
        """Get items with optional filters

        Args:
            status: Filter by status ('inbox', 'archived', 'starred', 'merged')
            collection_id: Filter by collection ID
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of Item objects ordered by creation date (newest first)
        """
        with self.get_session() as session:
            query = session.query(Item)

            if status:
                query = query.filter(Item.status == status)
            if collection_id:
                query = query.filter(Item.collection_id == collection_id)

            return query.order_by(Item.created_at.desc()).limit(limit).offset(offset).all()

    def update_item(self, item_id: str, **kwargs) -> Optional[Item]:
        """Update an item

        Args:
            item_id: Item UUID
            **kwargs: Fields to update

        Returns:
            Updated Item object or None if not found

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.get_session() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return None

                for key, value in kwargs.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                item.updated_at = datetime.now(timezone.utc)

                session.commit()
                session.refresh(item)
                return item
        except IntegrityError as e:
            raise DatabaseError(f"Failed to update item: {e}")

    def delete_item(self, item_id: str) -> bool:
        """Delete an item

        Also deletes associated tags and similarity records.

        Args:
            item_id: Item UUID

        Returns:
            True if item was deleted, False if not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.get_session() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return False

                # Delete associated tags and similarities
                session.query(ItemTag).filter(ItemTag.item_id == item_id).delete()
                session.query(ItemSimilarity).filter(
                    or_(ItemSimilarity.item_id_1 == item_id, ItemSimilarity.item_id_2 == item_id)
                ).delete()

                session.delete(item)
                session.commit()
                return True
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to delete item: {e}")

    def find_by_url(self, url: str) -> Optional[Item]:
        """Find an item by source URL

        Args:
            url: Source URL to search for

        Returns:
            Item object or None if not found
        """
        with self.get_session() as session:
            return session.query(Item).filter(Item.source_url == url).first()

    def search_items(
        self, query: str, limit: int = 20, use_meilisearch: bool = True
    ) -> List[Item]:
        """Full-text search in item content

        Uses Meilisearch if available, falls back to SQL LIKE.

        Args:
            query: Search query string
            limit: Maximum number of results
            use_meilisearch: Whether to use Meilisearch (if available)

        Returns:
            List of matching Item objects
        """
        # Try Meilisearch first
        if use_meilisearch:
            try:
                from kv.services.search_service import search_service

                if search_service.enabled:
                    results = search_service.search(query, limit=limit)
                    return [r.item for r in results]
            except Exception as e:
                # Fall back to SQLite if Meilisearch fails
                import logging
                logging.getLogger(__name__).warning(f"Meilisearch search failed, using fallback: {e}")

        # Fallback to SQL LIKE
        with self.get_session() as session:
            search_pattern = f"%{query}%"
            return (
                session.query(Item)
                .filter(
                    or_(
                        Item.title.like(search_pattern),
                        Item.content_text.like(search_pattern),
                    )
                )
                .filter(Item.status != "merged")
                .order_by(Item.created_at.desc())
                .limit(limit)
                .all()
            )

    # ========== Collection Operations ==========

    def create_collection(
        self, name: str, description: Optional[str] = None, parent_id: Optional[str] = None
    ) -> Collection:
        """Create a new collection

        Args:
            name: Collection name (must be unique)
            description: Optional description
            parent_id: Optional parent collection ID for hierarchy

        Returns:
            Created Collection object

        Raises:
            DuplicateCollectionError: If collection name already exists
            DatabaseError: If creation fails
        """
        try:
            with self.get_session() as session:
                collection = Collection(
                    id=str(uuid.uuid4()),
                    name=name,
                    description=description,
                    parent_id=parent_id,
                    item_count=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(collection)
                session.commit()
                session.refresh(collection)
                return collection
        except IntegrityError:
            raise DuplicateCollectionError(name)

    def get_collections(self, parent_id: Optional[str] = None) -> List[Collection]:
        """Get all collections, optionally filtered by parent

        Args:
            parent_id: Filter by parent collection ID (None for top-level)

        Returns:
            List of Collection objects ordered by name
        """
        with self.get_session() as session:
            query = session.query(Collection)
            if parent_id is not None:
                query = query.filter(Collection.parent_id == parent_id)
            return query.order_by(Collection.name).all()

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get a collection by ID

        Args:
            collection_id: Collection UUID

        Returns:
            Collection object or None if not found
        """
        with self.get_session() as session:
            return session.query(Collection).filter(Collection.id == collection_id).first()

    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        """Get a collection by name

        Args:
            name: Collection name

        Returns:
            Collection object or None if not found
        """
        with self.get_session() as session:
            return session.query(Collection).filter(Collection.name == name).first()

    def update_collection(self, collection_id: str, **kwargs) -> Optional[Collection]:
        """Update a collection

        Args:
            collection_id: Collection UUID
            **kwargs: Fields to update (name, description, parent_id)

        Returns:
            Updated Collection object or None if not found

        Raises:
            DuplicateCollectionError: If new name conflicts with existing collection
            DatabaseError: If update fails
        """
        try:
            with self.get_session() as session:
                collection = (
                    session.query(Collection).filter(Collection.id == collection_id).first()
                )
                if not collection:
                    return None

                for key, value in kwargs.items():
                    if hasattr(collection, key):
                        setattr(collection, key, value)

                collection.updated_at = datetime.now(timezone.utc)

                session.commit()
                session.refresh(collection)
                return collection
        except IntegrityError:
            raise DuplicateCollectionError(kwargs.get("name", ""))

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection

        Does not delete items, only unlinks them from the collection.

        Args:
            collection_id: Collection UUID

        Returns:
            True if collection was deleted, False if not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.get_session() as session:
                collection = (
                    session.query(Collection).filter(Collection.id == collection_id).first()
                )
                if not collection:
                    return False

                # Unlink items from this collection
                session.query(Item).filter(Item.collection_id == collection_id).update(
                    {"collection_id": None}
                )

                session.delete(collection)
                session.commit()
                return True
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to delete collection: {e}")

    # ========== Tag Operations ==========

    def create_tag(self, name: str, color: str = "#1B365D") -> Tag:
        """Create a new tag

        Args:
            name: Tag name (must be unique)
            color: Hex color code

        Returns:
            Created Tag object

        Raises:
            DuplicateTagError: If tag name already exists
            DatabaseError: If creation fails
        """
        try:
            with self.get_session() as session:
                tag = Tag(id=str(uuid.uuid4()), name=name, color=color, use_count=0)
                session.add(tag)
                session.commit()
                session.refresh(tag)
                return tag
        except IntegrityError:
            raise DuplicateTagError(name)

    def get_tags(self) -> List[Tag]:
        """Get all tags

        Returns:
            List of Tag objects ordered by use count (most used first)
        """
        with self.get_session() as session:
            return session.query(Tag).order_by(Tag.use_count.desc()).all()

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """Get a tag by ID

        Args:
            tag_id: Tag UUID

        Returns:
            Tag object or None if not found
        """
        with self.get_session() as session:
            return session.query(Tag).filter(Tag.id == tag_id).first()

    def find_tag_by_name(self, name: str) -> Optional[Tag]:
        """Find a tag by name

        Args:
            name: Tag name

        Returns:
            Tag object or None if not found
        """
        with self.get_session() as session:
            return session.query(Tag).filter(Tag.name == name).first()

    def update_tag(self, tag_id: str, **kwargs) -> Optional[Tag]:
        """Update a tag

        Args:
            tag_id: Tag UUID
            **kwargs: Fields to update (name, color)

        Returns:
            Updated Tag object or None if not found

        Raises:
            DuplicateTagError: If new name conflicts
            DatabaseError: If update fails
        """
        try:
            with self.get_session() as session:
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                if not tag:
                    return None

                for key, value in kwargs.items():
                    if hasattr(tag, key):
                        setattr(tag, key, value)

                session.commit()
                session.refresh(tag)
                return tag
        except IntegrityError:
            raise DuplicateTagError(kwargs.get("name", ""))

    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag

        Also removes all item-tag associations.

        Args:
            tag_id: Tag UUID

        Returns:
            True if tag was deleted, False if not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.get_session() as session:
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                if not tag:
                    return False

                # Delete item associations
                session.query(ItemTag).filter(ItemTag.tag_id == tag_id).delete()

                session.delete(tag)
                session.commit()
                return True
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to delete tag: {e}")

    def add_tag_to_item(self, item_id: str, tag_name: str) -> Tag:
        """Add a tag to an item (creates tag if it doesn't exist)

        Args:
            item_id: Item UUID
            tag_name: Tag name

        Returns:
            Tag object

        Raises:
            ItemNotFoundError: If item doesn't exist
            DatabaseError: If operation fails
        """
        try:
            with self.get_session() as session:
                # Verify item exists
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    raise ItemNotFoundError(item_id)

                # Find or create tag
                tag = session.query(Tag).filter(Tag.name == tag_name).first()

                if not tag:
                    tag = Tag(id=str(uuid.uuid4()), name=tag_name, use_count=0)
                    session.add(tag)
                else:
                    # Check if already tagged
                    existing = (
                        session.query(ItemTag)
                        .filter(
                            and_(ItemTag.item_id == item_id, ItemTag.tag_id == tag.id)
                        )
                        .first()
                    )
                    if existing:
                        return tag

                # Create association
                item_tag = ItemTag(item_id=item_id, tag_id=tag.id)
                session.add(item_tag)

                # Update use count
                tag.use_count = (session.query(ItemTag).filter(ItemTag.tag_id == tag.id).count()) + 1

                session.commit()
                session.refresh(tag)
                return tag
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to add tag to item: {e}")

    def remove_tag_from_item(self, item_id: str, tag_id: str) -> bool:
        """Remove a tag from an item

        Args:
            item_id: Item UUID
            tag_id: Tag UUID

        Returns:
            True if tag was removed, False if association didn't exist

        Raises:
            DatabaseError: If operation fails
        """
        try:
            with self.get_session() as session:
                item_tag = (
                    session.query(ItemTag)
                    .filter(and_(ItemTag.item_id == item_id, ItemTag.tag_id == tag_id))
                    .first()
                )

                if not item_tag:
                    return False

                session.delete(item_tag)

                # Update use count
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                if tag:
                    tag.use_count = session.query(ItemTag).filter(ItemTag.tag_id == tag_id).count()

                session.commit()
                return True
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to remove tag from item: {e}")

    def get_item_tags(self, item_id: str) -> List[Tag]:
        """Get all tags for an item

        Args:
            item_id: Item UUID

        Returns:
            List of Tag objects
        """
        with self.get_session() as session:
            return (
                session.query(Tag)
                .join(ItemTag, Tag.id == ItemTag.tag_id)
                .filter(ItemTag.item_id == item_id)
                .all()
            )

    # ========== Similarity Operations ==========

    def save_similarity(
        self, item_id_1: str, item_id_2: str, similarity: float, method: str = "simhash"
    ) -> ItemSimilarity:
        """Save a similarity score between two items

        Ensures consistent ordering (item_id_1 < item_id_2) to avoid duplicates.
        Updates existing record if one exists.

        Args:
            item_id_1: First item UUID
            item_id_2: Second item UUID
            similarity: Similarity score (0-1)
            method: Method used ('simhash', 'embedding')

        Returns:
            ItemSimilarity object

        Raises:
            DatabaseError: If operation fails
        """
        try:
            with self.get_session() as session:
                # Ensure consistent ordering
                if item_id_1 > item_id_2:
                    item_id_1, item_id_2 = item_id_2, item_id_1

                # Check if already exists
                existing = (
                    session.query(ItemSimilarity)
                    .filter(
                        and_(
                            ItemSimilarity.item_id_1 == item_id_1,
                            ItemSimilarity.item_id_2 == item_id_2,
                        )
                    )
                    .first()
                )

                if existing:
                    existing.similarity = similarity
                    existing.method = method
                    existing.computed_at = datetime.now(timezone.utc)
                    session.commit()
                    session.refresh(existing)
                    return existing

                similarity_record = ItemSimilarity(
                    item_id_1=item_id_1,
                    item_id_2=item_id_2,
                    similarity=similarity,
                    method=method,
                    computed_at=datetime.now(timezone.utc),
                )
                session.add(similarity_record)
                session.commit()
                session.refresh(similarity_record)
                return similarity_record
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to save similarity: {e}")

    def get_similar_items(
        self, item_id: str, threshold: float = 0.75
    ) -> List[tuple[Item, float]]:
        """Get items similar to the given item

        Args:
            item_id: Item UUID
            threshold: Minimum similarity score (0-1)

        Returns:
            List of (Item, similarity_score) tuples sorted by similarity descending
        """
        with self.get_session() as session:
            similarities = (
                session.query(ItemSimilarity)
                .filter(
                    and_(
                        or_(
                            ItemSimilarity.item_id_1 == item_id,
                            ItemSimilarity.item_id_2 == item_id,
                        ),
                        ItemSimilarity.similarity >= threshold,
                    )
                )
                .all()
            )

            results = []
            for sim in similarities:
                other_id = sim.item_id_2 if sim.item_id_1 == item_id else sim.item_id_1
                item = session.query(Item).filter(Item.id == other_id).first()
                if item:
                    results.append((item, sim.similarity))

            return sorted(results, key=lambda x: x[1], reverse=True)


# Global database service instance
db = DatabaseService()
