"""Update item content by re-scraping"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kv.services.database import db
from kv.services.scraper import scrape_url


def update_item(item_id: str):
    """Update an item by re-scraping its URL"""
    item = db.get_item(item_id)
    if not item:
        print(f"Item not found: {item_id}")
        return False

    if not item.source_url:
        print(f"Item has no URL: {item_id}")
        return False

    print(f"Re-scraping: {item.title}")
    print(f"URL: {item.source_url}")

    # Re-scrape
    scraped = scrape_url(item.source_url)

    # Update item using the update_item method
    db.update_item(
        item_id,
        title=scraped.title,
        content_html=scraped.content_html,
        content_text=scraped.content_text,
        author=scraped.author,
        word_count=scraped.word_count,
        reading_time=scraped.reading_time,
    )

    print(f"Updated: {scraped.title}")
    print(f"Word count: {scraped.word_count}")
    print(f"Content HTML length: {len(scraped.content_html)}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_item.py <item_id>")
        sys.exit(1)

    item_id = sys.argv[1]
    update_item(item_id)
