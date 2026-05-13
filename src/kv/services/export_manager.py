"""Export file management service with organized directory structure"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse


class ExportManager:
    """Manages exported files in an organized directory structure"""

    def __init__(self, export_dir: Optional[Path] = None):
        """
        Initialize export manager

        Args:
            export_dir: Root export directory (defaults to KNOWIT_HOME/exports)
        """
        from kv.core.config import config

        self.export_root = export_dir or (config.home_dir / "exports")
        self.export_root.mkdir(parents=True, exist_ok=True)

    def get_export_path(
        self,
        item_title: str,
        item_date: datetime,
        collection_name: Optional[str] = None,
        export_format: str = "html",
        organize_by: str = "date"
    ) -> Path:
        """
        Get the organized export path for an item

        Args:
            item_title: Item title
            item_date: Item creation date
            collection_name: Optional collection name
            export_format: File format (html/pdf)
            organize_by: Organization method (date/collection)

        Returns:
            Complete path for the exported file
        """
        # Generate safe filename from title
        safe_title = self._safe_filename(item_title)
        filename = f"{safe_title}.{export_format}"

        if organize_by == "collection" and collection_name:
            # Organize by collection: exports/by-collection/<collection>/<filename>
            collection_safe = self._safe_filename(collection_name)
            dir_path = self.export_root / "by-collection" / collection_safe
        elif organize_by == "date":
            # Organize by date: exports/YYYY-MM/YYYY-MM-DD_<title>.html
            date_str = item_date.strftime("%Y-%m")
            dir_path = self.export_root / date_str
            # Add date prefix to filename for better sorting
            date_prefix = item_date.strftime("%Y-%m-%d")
            filename = f"{date_prefix}_{safe_title}.{export_format}"
        else:
            # Flat structure in root
            dir_path = self.export_root

        # Create directory if needed
        dir_path.mkdir(parents=True, exist_ok=True)

        return dir_path / filename

    def get_relative_path(self, full_path: Path) -> Path:
        """Get path relative to export root"""
        try:
            return full_path.relative_to(self.export_root)
        except ValueError:
            return full_path

    def list_exports(
        self,
        pattern: str = "*",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all exported files

        Args:
            pattern: File pattern to match
            recursive: Whether to search recursively

        Returns:
            List of export info dicts
        """
        exports = []

        if recursive:
            files = self.export_root.rglob(pattern)
        else:
            files = self.export_root.glob(pattern)

        for file_path in files:
            if file_path.is_file():
                stat = file_path.stat()
                exports.append({
                    "path": str(file_path),
                    "relative_path": str(self.get_relative_path(file_path)),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "format": file_path.suffix.lstrip('.'),
                })

        # Sort by modified time descending
        exports.sort(key=lambda x: x["modified"], reverse=True)

        return exports

    def clean_old_exports(
        self,
        keep_days: int = 30,
        keep_count: Optional[int] = None,
        dry_run: bool = False
    ) -> List[Path]:
        """
        Clean old exported files

        Args:
            keep_days: Keep files newer than this many days
            keep_count: Keep at most this many files per directory
            dry_run: If True, only report what would be deleted

        Returns:
            List of files that were (or would be) deleted
        """
        deleted_files = []
        cutoff_date = datetime.now().timestamp() - (keep_days * 86400)

        # Clean by date
        for file_path in self.export_root.rglob("*.html"):
            if file_path.is_file():
                stat = file_path.stat()

                # Check age
                if stat.st_mtime < cutoff_date:
                    deleted_files.append(file_path)
                    if not dry_run:
                        file_path.unlink()

        # Clean by count per directory
        if keep_count:
            for dir_path in self.export_root.rglob("*"):
                if dir_path.is_dir():
                    # Get all HTML files in this directory
                    files = list(dir_path.glob("*.html"))
                    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                    # Remove old files beyond keep_count
                    for file_path in files[keep_count:]:
                        if file_path not in deleted_files:
                            deleted_files.append(file_path)
                            if not dry_run:
                                file_path.unlink()

        return deleted_files

    def clean_all(self, dry_run: bool = False) -> List[Path]:
        """
        Clean all exported files

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            List of files that were (or would be) deleted
        """
        deleted_files = []

        for file_path in self.export_root.rglob("*"):
            if file_path.is_file():
                deleted_files.append(file_path)
                if not dry_run:
                    file_path.unlink()

        return deleted_files

    def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics about exported files"""
        exports = self.list_exports()

        total_size = sum(e["size"] for e in exports)
        by_format = {}
        by_date = {}

        for export in exports:
            fmt = export["format"]
            by_format[fmt] = by_format.get(fmt, 0) + 1

            date_key = export["created"].strftime("%Y-%m")
            by_date[date_key] = by_date.get(date_key, 0) + 1

        return {
            "total_count": len(exports),
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "by_format": by_format,
            "by_date": by_date,
            "export_root": str(self.export_root),
        }

    def _safe_filename(self, name: str, max_length: int = 100) -> str:
        """
        Convert string to safe filename

        Args:
            name: Original name
            max_length: Maximum filename length

        Returns:
            Safe filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')

        # Remove leading/trailing spaces and dots
        name = name.strip('. ')

        # Limit length
        if len(name) > max_length:
            name = name[:max_length]

        # Ensure non-empty
        if not name:
            name = "untitled"

        return name

    def get_export_root(self) -> Path:
        """Get the export root directory"""
        return self.export_root


# Global export manager instance
export_manager = ExportManager()
