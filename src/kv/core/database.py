"""数据库模型"""

from sqlalchemy import Column, String, Integer, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

# Helper function for UTC timestamps
def utcnow():
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


class Item(Base):
    """知识条目表"""

    __tablename__ = "items"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # 'webpage', 'wechat', 'local', 'manual'
    source_url = Column(String)
    author = Column(String)
    content_html = Column(Text)
    content_markdown = Column(Text)
    content_text = Column(Text)
    word_count = Column(Integer)
    reading_time = Column(Integer)
    collection_id = Column(String, ForeignKey("collections.id"))
    status = Column(String, default="inbox")  # 'inbox', 'archived', 'starred', 'merged'
    merged_into = Column(String, ForeignKey("items.id"))
    simhash = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Collection(Base):
    """知识合集表"""

    __tablename__ = "collections"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(String, ForeignKey("collections.id"))
    item_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Tag(Base):
    """标签表"""

    __tablename__ = "tags"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    color = Column(String, default="#1B365D")
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)


class ItemTag(Base):
    """条目标签关联表"""

    __tablename__ = "item_tags"

    item_id = Column(String, ForeignKey("items.id"), primary_key=True)
    tag_id = Column(String, ForeignKey("tags.id"), primary_key=True)


class ItemSimilarity(Base):
    """相似度缓存表"""

    __tablename__ = "item_similarities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id_1 = Column(String, ForeignKey("items.id"), nullable=False)
    item_id_2 = Column(String, ForeignKey("items.id"), nullable=False)
    similarity = Column(Float, nullable=False)
    method = Column(String, nullable=False)  # 'simhash', 'embedding'
    computed_at = Column(DateTime, default=utcnow)
