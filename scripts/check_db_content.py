"""Check database content"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kv.services.database import db


def check_item(item_id: str):
    """Check item content in database"""
    item = db.get_item(item_id)
    if not item:
        print(f"Item not found: {item_id}")
        return

    print(f"Title: {item.title}")
    print(f"Author: {item.author}")
    print(f"Word count: {item.word_count}")
    print(f"Reading time: {item.reading_time}")
    print(f"Content HTML length: {len(item.content_html) if item.content_html else 0}")
    print(f"Content text length: {len(item.content_text) if item.content_text else 0}")

    if item.content_html:
        print(f"\nFirst 500 chars of HTML:")
        print(item.content_html[:500])

    if item.content_text:
        print(f"\nFirst 500 chars of text:")
        print(item.content_text[:500])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_db_content.py <item_id>")
        sys.exit(1)

    item_id = sys.argv[1]
    check_item(item_id)
