"""Test WeChat scraper"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kv.services.scraper import scrape_url


def test_wechat():
    """Test scraping a WeChat article"""
    url = "https://mp.weixin.qq.com/s/LCpiLyLnRn5WyuHpribyHw"

    print(f"Scraping: {url}")
    scraped = scrape_url(url)

    print(f"\nTitle: {scraped.title}")
    print(f"Author: {scraped.author}")
    print(f"Word count: {scraped.word_count}")
    print(f"Content HTML length: {len(scraped.content_html)}")
    print(f"Content text length: {len(scraped.content_text)}")

    # Show first 500 chars of HTML
    print(f"\nFirst 500 chars of HTML:")
    print(scraped.content_html[:500])

    # Show first 500 chars of text
    print(f"\nFirst 500 chars of text:")
    print(scraped.content_text[:500])

    # Save to file for inspection
    output_file = Path("wechat_scraped_content.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(scraped.content_html)
    print(f"\nFull HTML saved to: {output_file}")


if __name__ == "__main__":
    test_wechat()
