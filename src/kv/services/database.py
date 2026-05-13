"""Database service layer for CRUD operations"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from kv.core.config import config
from kv.core.database import Base, Item, Collection, Tag, ItemTag, ItemSimilarity


class DatabaseService:
    """Database service for managing knowledge items"""

    def __init__(self):
        self.engine = create_engine(f"sqlite:///{config.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(self.engine)

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
        """Create a new knowledge item"""
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
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(item)
            try:
                session.commit()
                session.refresh(item)
                return item
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Failed to create item: {e}")

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID"""
        with self.get_session() as session:
            return session.query(Item).filter(Item.id == item_id).first()

    def get_items(
        self,
        status: Optional[str] = None,
        collection_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Item]:
        """Get items with optional filters"""
        with self.get_session() as session:
            query = session.query(Item)

            if status:
                query = query.filter(Item.status == status)
            if collection_id:
                query = query.filter(Item.collection_id == collection_id)

            return query.order_by(Item.created_at.desc()).limit(limit).offset(offset).all()

    def update_item(self, item_id: str, **kwargs) -> Optional[Item]:
        """Update an item"""
        with self.get_session() as session:
            item = session.query(Item).filter(Item.id == item_id).first()
            if not item:
                return None

            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            item.updated_at = datetime.utcnow()

            try:
                session.commit()
                session.refresh(item)
                return item
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Failed to update item: {e}")

    def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
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

    def find_by_url(self, url: str) -> Optional[Item]:
        """Find an item by source URL"""
        with self.get_session() as session:
            return session.query(Item).filter(Item.source_url == url).first()

    def search_items(self, query: str, limit: int = 20) -> List[Item]:
        """Full-text search in item content"""
        with self.get_session() as session:
            # Simple text search using LIKE (can be upgraded to Meilisearch)
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
        """Create a new collection"""
        with self.get_session() as session:
            collection = Collection(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                parent_id=parent_id,
                item_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(collection)
            try:
                session.commit()
                session.refresh(collection)
                return collection
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Collection name already exists: {e}")

    def get_collections(self, parent_id: Optional[str] = None) -> List[Collection]:
        """Get all collections, optionally filtered by parent"""
        with self.get_session() as session:
            query = session.query(Collection)
            if parent_id is not None:
                query = query.filter(Collection.parent_id == parent_id)
            return query.order_by(Collection.name).all()

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get a collection by ID"""
        with self.get_session() as session:
            return session.query(Collection).filter(Collection.id == collection_id).first()

    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        """Get a collection by name"""
        with self.get_session() as session:
            return session.query(Collection).filter(Collection.name == name).first()

    def update_collection(self, collection_id: str, **kwargs) -> Optional[Collection]:
        """Update a collection"""
        with self.get_session() as session:
            collection = (
                session.query(Collection).filter(Collection.id == collection_id).first()
            )
            if not collection:
                return None

            for key, value in kwargs.items():
                if hasattr(collection, key):
                    setattr(collection, key, value)

            collection.updated_at = datetime.utcnow()

            try:
                session.commit()
                session.refresh(collection)
                return collection
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Failed to update collection: {e}")

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection (doesn't delete items, just unlinks them)"""
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

    # ========== Tag Operations ==========

    def create_tag(self, name: str, color: str = "#1B365D") -> Tag:
        """Create a new tag"""
        with self.get_session() as session:
            tag = Tag(id=str(uuid.uuid4()), name=name, color=color, use_count=0)
            session.add(tag)
            try:
                session.commit()
                session.refresh(tag)
                return tag
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Tag name already exists: {e}")

    def get_tags(self) -> List[Tag]:
        """Get all tags"""
        with self.get_session() as session:
            return session.query(Tag).order_by(Tag.use_count.desc()).all()

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """Get a tag by ID"""
        with self.get_session() as session:
            return session.query(Tag).filter(Tag.id == tag_id).first()

    def find_tag_by_name(self, name: str) -> Optional[Tag]:
        """Find a tag by name"""
        with self.get_session() as session:
            return session.query(Tag).filter(Tag.name == name).first()

    def update_tag(self, tag_id: str, **kwargs) -> Optional[Tag]:
        """Update a tag"""
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

    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag"""
        with self.get_session() as session:
            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                return False

            # Delete item associations
            session.query(ItemTag).filter(ItemTag.tag_id == tag_id).delete()

            session.delete(tag)
            session.commit()
            return True

    def add_tag_to_item(self, item_id: str, tag_name: str) -> Tag:
        """Add a tag to an item (creates tag if it doesn't exist)"""
        with self.get_session() as session:
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

    def remove_tag_from_item(self, item_id: str, tag_id: str) -> bool:
        """Remove a tag from an item"""
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

    def get_item_tags(self, item_id: str) -> List[Tag]:
        """Get all tags for an item"""
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
        """Save a similarity score between two items"""
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
                existing.computed_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing

            similarity_record = ItemSimilarity(
                item_id_1=item_id_1,
                item_id_2=item_id_2,
                similarity=similarity,
                method=method,
                computed_at=datetime.utcnow(),
            )
            session.add(similarity_record)
            session.commit()
            session.refresh(similarity_record)
            return similarity_record

    def get_similar_items(self, item_id: str, threshold: float = 0.75) -> List[tuple[Item, float]]:
        """Get items similar to the given item"""
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
