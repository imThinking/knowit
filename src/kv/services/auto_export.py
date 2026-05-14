"""Automatic export service for knowledge items

Exports items to HTML and PDF formats automatically after adding.
"""

import click
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from kv.core.database import Item
from kv.services.pdf_export import html_exporter
from kv.services.export_manager import export_manager
from kv.services.config_service import config_service


class AutoExportService:
    """Automatic export service for knowledge items"""

    def __init__(self):
        """Initialize auto export service"""
        self.config_service = config_service
        self.exporter = html_exporter
        self.export_manager = export_manager

    def should_export(self) -> bool:
        """
        Check if auto-export is enabled in configuration

        Returns:
            True if auto-export is enabled
        """
        enabled = self.config_service.get("auto_export.enabled", True)
        return bool(enabled)

    def get_export_formats(self) -> List[str]:
        """
        Get list of export formats from configuration

        Returns:
            List of formats (e.g., ["html", "pdf"])
        """
        formats = self.config_service.get("auto_export.formats", ["html", "pdf"])
        if not isinstance(formats, list):
            return ["html", "pdf"]
        # Validate formats
        return [f for f in formats if f in ("html", "pdf")]

    def export_item(self, item: Item) -> Dict[str, Optional[str]]:
        """
        Export a single knowledge item to configured formats

        Args:
            item: Item object from database

        Returns:
            Dict with keys: "html", "pdf", "error"
            Values are file paths (str) or None if export failed
        """
        results = {}

        # Get configuration
        clean_html = self.config_service.get("auto_export.clean_html", True)
        use_kami = self.config_service.get("auto_export.use_kami", True)
        organize_by = self.config_service.get("auto_export.organize_by", "collection")

        # Get collection name
        collection_name = None
        if item.collection_id:
            from kv.services.database import db
            try:
                collection = db.get_collection(item.collection_id)
                collection_name = collection.name if collection else "Uncategorized"
            except Exception:
                collection_name = "Uncategorized"

        if not collection_name:
            collection_name = "Inbox"

        # Determine export formats
        formats = self.get_export_formats()

        # Export each format
        for fmt in formats:
            try:
                # Generate export path
                export_path = self.export_manager.get_export_path(
                    item_title=item.title,
                    item_date=item.created_at or datetime.now(),
                    collection_name=collection_name,
                    export_format=fmt,
                    organize_by=organize_by
                )

                # Call appropriate export method
                if fmt == "html":
                    if use_kami:
                        # Full Kami format with cover page
                        self.exporter.generate_html(
                            title=item.title,
                            content=item.content_html or item.content_text or "",
                            author=item.author,
                            url=item.source_url,
                            created_at=item.created_at,
                            output_path=str(export_path),
                            clean=clean_html
                        )
                    else:
                        # Simple format without cover page
                        self.exporter.generate_html_simple(
                            title=item.title,
                            content=item.content_html or item.content_text or "",
                            author=item.author,
                            url=item.source_url,
                            created_at=item.created_at,
                            output_path=str(export_path),
                            clean=clean_html
                        )

                elif fmt == "pdf":
                    self.exporter.generate_pdf(
                        title=item.title,
                        content=item.content_html or item.content_text or "",
                        author=item.author,
                        url=item.source_url,
                        created_at=item.created_at,
                        output_path=str(export_path),
                        clean=clean_html
                    )

                results[fmt] = str(export_path)

            except Exception as e:
                results[fmt] = None
                if "error" not in results:
                    results["error"] = str(e)

        return results

    def handle_export_error(self, error: Exception, item_title: str):
        """
        Handle export errors based on configuration

        Args:
            error: Exception that occurred
            item_title: Title of the item being exported
        """
        on_error = self.config_service.get("auto_export.on_error", "warn")

        if on_error == "warn":
            click.echo(f"\n[警告] 自动导出失败 ({item_title}): {error}", err=True)
        # on_error == "ignore" -> silent


# Global auto export service instance
auto_export_service = AutoExportService()
