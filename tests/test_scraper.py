"""Tests for web scraper service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout as RequestsTimeout, RequestException

from kv.services.scraper import WebScraper, ScrapedContent, scrape_file, generate_simhash
from kv.core.exceptions import NetworkError


class TestWebScraper:
    """Test WebScraper class"""

    def test_init(self):
        """Test scraper initialization"""
        scraper = WebScraper(timeout=60)
        assert scraper.timeout == 60
        assert scraper.session is not None
        assert "User-Agent" in scraper.session.headers

    def test_validate_url_valid(self):
        """Test URL validation with valid URLs"""
        scraper = WebScraper()
        assert scraper.validate_url("https://example.com") is True
        assert scraper.validate_url("http://test.org/path?query=1") is True

    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs"""
        scraper = WebScraper()
        assert scraper.validate_url("not-a-url") is False
        assert scraper.validate_url("") is False
        assert scraper.validate_url("example.com") is False  # Missing scheme

    @patch('kv.services.scraper.requests.Session.get')
    def test_fetch_success(self, mock_get, sample_html_content):
        """Test successful content fetching"""
        # Mock response
        mock_response = Mock()
        mock_response.text = sample_html_content
        mock_response.apparent_encoding = 'utf-8'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scraper = WebScraper()
        result = scraper.fetch("https://example.com")

        assert isinstance(result, ScrapedContent)
        assert result.title == "OG Title"  # From og:title meta
        assert result.author == "John Doe"  # From meta author
        assert "sample paragraph" in result.content_text.lower()
        assert result.word_count > 0
        assert result.reading_time > 0

    @patch('kv.services.scraper.requests.Session.get')
    def test_fetch_timeout(self, mock_get):
        """Test handling of timeout errors"""
        mock_get.side_effect = RequestsTimeout()

        scraper = WebScraper()
        from kv.core.exceptions import TimeoutError
        with pytest.raises(TimeoutError):
            scraper.fetch("https://example.com")

    @patch('kv.services.scraper.requests.Session.get')
    def test_fetch_network_error(self, mock_get):
        """Test handling of network errors"""
        mock_get.side_effect = RequestException("Connection failed")

        scraper = WebScraper()
        with pytest.raises(NetworkError):
            scraper.fetch("https://example.com")

    def test_extract_title(self, sample_html_content):
        """Test title extraction from HTML"""
        scraper = WebScraper()
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html_content, 'lxml')
        title = scraper._extract_title(soup)

        # Should prefer og:title
        assert title == "OG Title"

    def test_extract_author(self, sample_html_content):
        """Test author extraction from HTML"""
        scraper = WebScraper()
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html_content, 'lxml')
        author = scraper._extract_author(soup)

        assert author == "John Doe"

    def test_calculate_reading_time(self):
        """Test reading time calculation"""
        scraper = WebScraper()

        # 200 words = 1 minute (default WPM)
        assert scraper._calculate_reading_time(200) == 1
        assert scraper._calculate_reading_time(400) == 2
        assert scraper._calculate_reading_time(0) == 0
        assert scraper._calculate_reading_time(50) == 1  # Minimum 1 minute

    def test_html_to_text(self):
        """Test HTML to text conversion"""
        scraper = WebScraper()
        html = "<p>First paragraph</p><p>Second paragraph</p>"
        text = scraper._html_to_text(html)

        assert "First paragraph" in text
        assert "Second paragraph" in text
        assert "<p>" not in text


class TestScrapedContent:
    """Test ScrapedContent class"""

    def test_init(self):
        """Test ScrapedContent initialization"""
        content = ScrapedContent(
            title="Test",
            content_html="<p>Test</p>",
            content_text="Test",
            author="Author",
            word_count=100,
            reading_time=1,
        )

        assert content.title == "Test"
        assert content.content_html == "<p>Test</p>"
        assert content.author == "Author"
        assert content.word_count == 100
        assert content.reading_time == 1


class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_simhash(self):
        """Test simhash generation"""
        hash1 = generate_simhash("test content")
        hash2 = generate_simhash("test content")
        hash3 = generate_simhash("different content")

        # Same content should produce same hash
        assert hash1 == hash2
        # Different content should produce different hash
        assert hash1 != hash3
        # Hash should be hex string
        assert all(c in '0123456789abcdef' for c in hash1)

    def test_scrape_file_success(self, tmp_path):
        """Test file scraping with real file"""
        # Create a temporary HTML file
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><head><title>Test Title</title></head><body><p>Test content here</p></body></html>")

        result = scrape_file(str(html_file))

        assert isinstance(result, ScrapedContent)
        assert result.title == "Test Title"
        assert "Test content here" in result.content_text
