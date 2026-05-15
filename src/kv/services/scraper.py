"""Web scraping service for fetching and parsing web content"""

import re
from typing import Optional
from urllib.parse import urlparse
import hashlib

from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException, Timeout as RequestsTimeout

from kv.core.exceptions import (
    ScrapingError,
    InvalidURLError,
    NetworkError,
    TimeoutError,
    ContentExtractionError,
    PlaywrightError,
    FileReadError,
)


class ScrapedContent:
    """Container for scraped content"""

    def __init__(
        self,
        title: str,
        content_html: str,
        content_text: str,
        author: Optional[str] = None,
        word_count: Optional[int] = None,
        reading_time: Optional[int] = None,
    ):
        self.title = title
        self.content_html = content_html
        self.content_text = content_text
        self.author = author
        self.word_count = word_count
        self.reading_time = reading_time


class WebScraper:
    """Web scraper using requests + BeautifulSoup

    Provides methods for fetching and parsing web content,
    including title extraction, author detection, and content cleaning.

    Attributes:
        timeout: Request timeout in seconds
        session: Requests session for connection pooling
    """

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the web scraper

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def fetch(self, url: str) -> ScrapedContent:
        """Fetch and parse content from a URL

        Args:
            url: URL to fetch and parse

        Returns:
            ScrapedContent object containing parsed content

        Raises:
            InvalidURLError: If URL is malformed
            TimeoutError: If request times out
            NetworkError: If network request fails
            ContentExtractionError: If content cannot be extracted
        """
        # Validate URL
        if not self.validate_url(url):
            raise InvalidURLError(url, "Malformed URL")

        # Check if this is a WeChat article - use Playwright for dynamic content
        if "mp.weixin.qq.com" in url:
            return self._fetch_wechat_article(url)

        # Regular scraping with requests
        return self._fetch_with_requests(url)

    def _fetch_wechat_article(self, url: str) -> ScrapedContent:
        """Fetch WeChat article using Playwright

        Args:
            url: WeChat article URL

        Returns:
            ScrapedContent object

        Raises:
            PlaywrightError: If Playwright scraping fails
        """
        try:
            from .playwright_scraper import scrape_wechat_article
            data = scrape_wechat_article(url)

            # Convert dict to ScrapedContent
            content_text = self._html_to_text(data["html"])
            word_count = len(content_text.split()) if content_text else 0

            return ScrapedContent(
                title=data["title"],
                content_html=data["html"],
                content_text=content_text,
                author=data["author"],
                word_count=word_count,
                reading_time=self._calculate_reading_time(word_count),
            )
        except Exception as e:
            # Fallback to regular scraping if Playwright fails
            raise PlaywrightError(url, str(e))

    def _fetch_with_requests(self, url: str) -> ScrapedContent:
        """Fetch content using requests library

        Args:
            url: URL to fetch

        Returns:
            ScrapedContent object

        Raises:
            TimeoutError: If request times out
            NetworkError: If network request fails
            ContentExtractionError: If content cannot be extracted
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
        except RequestsTimeout:
            raise TimeoutError(url, self.timeout)
        except RequestException as e:
            raise NetworkError(url, reason=str(e))

        try:
            soup = BeautifulSoup(response.text, "lxml")

            # Extract title
            title = self._extract_title(soup)

            # Extract author
            author = self._extract_author(soup)

            # Remove unwanted elements
            self._cleanup_soup(soup)

            # Extract main content
            content_html = self._extract_content(soup)

            # Extract text
            content_text = self._html_to_text(content_html)

            # Calculate word count and reading time
            word_count = len(content_text.split()) if content_text else 0
            reading_time = self._calculate_reading_time(word_count)

            return ScrapedContent(
                title=title,
                content_html=content_html,
                content_text=content_text,
                author=author,
                word_count=word_count,
                reading_time=reading_time,
            )
        except Exception as e:
            raise ContentExtractionError(url, str(e))

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from the page

        Tries multiple sources in order:
        1. Open Graph title (og:title)
        2. HTML title tag
        3. First h1 tag
        4. Fallback to "Untitled"

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted title
        """
        # Try og:title first
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # Try h1
        h1 = soup.find("h1")
        if h1 and h1.string:
            return h1.string.strip()

        return "Untitled"

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from the page

        Tries multiple sources:
        1. Meta author tag
        2. Open Graph article:author
        3. Schema.org author span

        Args:
            soup: BeautifulSoup object

        Returns:
            Author name or None if not found
        """
        # Try meta author
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()

        # Try og:article:author
        og_author = soup.find("meta", property="article:author")
        if og_author and og_author.get("content"):
            return og_author["content"].strip()

        # Try schema.org author
        author_span = soup.find("span", attrs={"itemprop": "author"})
        if author_span:
            return author_span.get_text().strip()

        return None

    def _cleanup_soup(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from the page

        Removes scripts, styles, iframes, and other non-content elements.

        Args:
            soup: BeautifulSoup object to clean
        """
        # Elements to remove
        unwanted_tags = [
            "script",
            "style",
            "iframe",
            "noscript",
        ]

        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content from the page

        Tries multiple selectors to find main content:
        1. <article> tag
        2. Common content container selectors
        3. Fallback to <body>

        Args:
            soup: BeautifulSoup object

        Returns:
            HTML string of main content
        """
        # Try to find article tag
        article = soup.find("article")
        if article:
            return str(article)

        # Try common content containers
        content_selectors = [
            "main",
            '[role="main"]',
            ".content",
            ".post-content",
            ".article-content",
            ".entry-content",
            "#content",
            "#main",
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return str(element)

        # Fallback to body
        body = soup.find("body")
        if body:
            return str(body)

        return ""

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text

        Extracts text content from HTML while preserving paragraph structure.

        Args:
            html: HTML string

        Returns:
            Plain text with preserved structure
        """
        soup = BeautifulSoup(html, "lxml")

        # Replace block elements with newlines
        for tag in soup.find_all(["p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6"]):
            tag.insert_after("\n")

        text = soup.get_text()

        # Clean up whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = text.strip()

        return text

    def _calculate_reading_time(self, word_count: int, wpm: int = 200) -> int:
        """Calculate reading time in minutes

        Args:
            word_count: Number of words
            wpm: Reading speed (words per minute)

        Returns:
            Reading time in minutes (minimum 1)
        """
        if word_count == 0:
            return 0
        return max(1, round(word_count / wpm))

    def validate_url(self, url: str) -> bool:
        """Validate if a URL is well-formed

        Args:
            url: URL string to validate

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


def scrape_file(file_path: str) -> ScrapedContent:
    """Scrape content from a local file

    Args:
        file_path: Path to the local HTML file

    Returns:
        ScrapedContent object

    Raises:
        FileReadError: If file cannot be read
        ContentExtractionError: If content cannot be extracted
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        raise FileReadError(file_path, str(e))

    scraper = WebScraper()
    soup = BeautifulSoup(content, "lxml")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text() if title_tag else file_path

    # Extract author
    author_meta = soup.find("meta", attrs={"name": "author"})
    author = author_meta["content"] if author_meta else None

    # Remove unwanted elements
    scraper._cleanup_soup(soup)

    # Extract content
    content_html = scraper._extract_content(soup)

    # Extract text
    content_text = scraper._html_to_text(content_html)

    # Calculate word count and reading time
    word_count = len(content_text.split()) if content_text else 0
    reading_time = scraper._calculate_reading_time(word_count)

    return ScrapedContent(
        title=title,
        content_html=content_html,
        content_text=content_text,
        author=author,
        word_count=word_count,
        reading_time=reading_time,
    )


def generate_simhash(text: str) -> str:
    """Generate a simple hash for text (placeholder for simhash library)

    Note: This is a simplified version using MD5.
    Use the simhash library for production deduplication.

    Args:
        text: Text to hash

    Returns:
        Hex string hash
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def scrape_url(url: str) -> ScrapedContent:
    """Convenience function to scrape a URL

    Args:
        url: URL to scrape

    Returns:
        ScrapedContent object

    Raises:
        InvalidURLError: If URL is invalid
        TimeoutError: If request times out
        NetworkError: If network request fails
        ContentExtractionError: If content cannot be extracted
    """
    scraper = WebScraper()
    return scraper.fetch(url)
