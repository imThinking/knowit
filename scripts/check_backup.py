"""Check backup database content"""

import sys
from pathlib import Path
import sqlite3

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kv.core.config import config
from kv.core.database import Item


def check_backup(backup_path: str, item_id: str):
    """Check item content in backup database"""
    conn = sqlite3.connect(backup_path)

    # Query the item
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, word_count, reading_time, length(content_html), length(content_text) FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()

    if row:
        print(f"Item found in backup:")
        print(f"ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Author: {row[2]}")
        print(f"Word count: {row[3]}")
        print(f"Reading time: {row[4]}")
        print(f"Content HTML length: {row[5]}")
        print(f"Content text length: {row[6]}")

        # Get the actual content
        cursor.execute("SELECT content_html, content_text FROM items WHERE id = ?", (item_id,))
        html, text = cursor.fetchone()

        if html:
            print(f"\nFirst 500 chars of HTML:")
            print(html[:500])

        if text:
            print(f"\nFirst 500 chars of text:")
            print(text[:500])
    else:
        print(f"Item not found in backup: {item_id}")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_backup.py <backup_path> <item_id>")
        sys.exit(1)

    backup_path = sys.argv[1]
    item_id = sys.argv[2]
    check_backup(backup_path, item_id)
