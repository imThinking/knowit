"""Custom exceptions for KnowIt application

This module defines all custom exceptions used throughout the application.
Exceptions are organized by category (database, scraping, export, etc.)
for better error handling and user messaging.
"""

from typing import Optional, Any


class KnowItError(Exception):
    """Base exception for all KnowIt errors

    Attributes:
        message: Human-readable error message
        details: Optional dict with additional error context
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


# ========== Database Exceptions ==========

class DatabaseError(KnowItError):
    """Base exception for database-related errors"""

    pass


class ItemNotFoundError(DatabaseError):
    """Raised when an item cannot be found"""

    def __init__(self, item_id: str):
        super().__init__(f"Item not found: {item_id}", {"item_id": item_id})


class CollectionNotFoundError(DatabaseError):
    """Raised when a collection cannot be found"""

    def __init__(self, collection_id: str):
        super().__init__(f"Collection not found: {collection_id}", {"collection_id": collection_id})


class TagNotFoundError(DatabaseError):
    """Raised when a tag cannot be found"""

    def __init__(self, tag_id: str):
        super().__init__(f"Tag not found: {tag_id}", {"tag_id": tag_id})


class DuplicateItemError(DatabaseError):
    """Raised when attempting to create a duplicate item"""

    def __init__(self, field: str, value: str):
        super().__init__(
            f"Item already exists with {field}: {value}",
            {"field": field, "value": value}
        )


class DuplicateCollectionError(DatabaseError):
    """Raised when attempting to create a collection with duplicate name"""

    def __init__(self, name: str):
        super().__init__(f"Collection already exists: {name}", {"name": name})


class DuplicateTagError(DatabaseError):
    """Raised when attempting to create a tag with duplicate name"""

    def __init__(self, name: str):
        super().__init__(f"Tag already exists: {name}", {"name": name})


# ========== Scraping Exceptions ==========

class ScrapingError(KnowItError):
    """Base exception for web scraping errors"""

    pass


class InvalidURLError(ScrapingError):
    """Raised when a URL is invalid or malformed"""

    def __init__(self, url: str, reason: str = ""):
        message = f"Invalid URL: {url}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"url": url, "reason": reason})


class NetworkError(ScrapingError):
    """Raised when network request fails"""

    def __init__(self, url: str, status_code: Optional[int] = None, reason: str = ""):
        message = f"Network error accessing {url}"
        if status_code:
            message += f" (status: {status_code})"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"url": url, "status_code": status_code, "reason": reason})


class TimeoutError(ScrapingError):
    """Raised when request times out"""

    def __init__(self, url: str, timeout: int):
        super().__init__(
            f"Request timeout after {timeout}s: {url}",
            {"url": url, "timeout": timeout}
        )


class ContentExtractionError(ScrapingError):
    """Raised when content cannot be extracted from page"""

    def __init__(self, url: str, reason: str = "Could not extract main content"):
        super().__init__(f"{reason}: {url}", {"url": url, "reason": reason})


class PlaywrightError(ScrapingError):
    """Raised when Playwright dynamic scraping fails"""

    def __init__(self, url: str, reason: str = ""):
        message = f"Playwright error for {url}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"url": url, "reason": reason})


# ========== Export Exceptions ==========

class ExportError(KnowItError):
    """Base exception for export-related errors"""

    pass


class TemplateNotFoundError(ExportError):
    """Raised when export template cannot be found"""

    def __init__(self, template_path: str):
        super().__init__(f"Template not found: {template_path}", {"template_path": template_path})


class PDFGenerationError(ExportError):
    """Raised when PDF generation fails"""

    def __init__(self, reason: str = "", details: Optional[dict[str, Any]] = None):
        message = "PDF generation failed"
        if reason:
            message += f": {reason}"
        super().__init__(message, details or {"reason": reason})


class FontNotFoundError(ExportError):
    """Raised when required font cannot be found"""

    def __init__(self, font_name: str):
        super().__init__(f"Font not found: {font_name}", {"font_name": font_name})


class WeasyPrintNotFoundError(ExportError):
    """Raised when WeasyPrint is not installed"""

    def __init__(self):
        super().__init__(
            "WeasyPrint is not installed. Run: pip install weasyprint",
            {"install_command": "pip install weasyprint"}
        )


# ========== Configuration Exceptions ==========

class ConfigurationError(KnowItError):
    """Base exception for configuration errors"""

    pass


class InvalidConfigPathError(ConfigurationError):
    """Raised when config path is invalid"""

    def __init__(self, path: str):
        super().__init__(f"Invalid configuration path: {path}", {"path": path})


class ConfigValidationError(ConfigurationError):
    """Raised when configuration value is invalid"""

    def __init__(self, key: str, value: Any, reason: str = ""):
        message = f"Invalid configuration value for {key}: {value}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"key": key, "value": value, "reason": reason})


# ========== Deduplication Exceptions ==========

class DeduplicationError(KnowItError):
    """Base exception for deduplication errors"""

    pass


class SimhashComputationError(DeduplicationError):
    """Raised when simhash computation fails"""

    def __init__(self, reason: str = ""):
        message = "Failed to compute simhash"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"reason": reason})


# ========== File System Exceptions ==========

class FileSystemError(KnowItError):
    """Base exception for file system errors"""

    pass


class FileReadError(FileSystemError):
    """Raised when file cannot be read"""

    def __init__(self, path: str, reason: str = ""):
        message = f"Cannot read file: {path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"path": path, "reason": reason})


class FileWriteError(FileSystemError):
    """Raised when file cannot be written"""

    def __init__(self, path: str, reason: str = ""):
        message = f"Cannot write file: {path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"path": path, "reason": reason})


class DirectoryNotFoundError(FileSystemError):
    """Raised when directory does not exist"""

    def __init__(self, path: str):
        super().__init__(f"Directory not found: {path}", {"path": path})


# ========== Search Exceptions ==========

class SearchError(KnowItError):
    """Base exception for search-related errors"""

    pass


class MeilisearchConnectionError(SearchError):
    """Raised when cannot connect to Meilisearch"""

    def __init__(self, url: str, reason: str = ""):
        message = f"Cannot connect to Meilisearch at {url}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            {"url": url, "reason": reason, "hint": "Ensure Meilisearch is running or check KNOWIT_MEILISEARCH_URL"}
        )


class MeilisearchIndexError(SearchError):
    """Raised when Meilisearch index operation fails"""

    def __init__(self, index: str, reason: str = ""):
        message = f"Meilisearch index error: {index}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"index": index, "reason": reason})
