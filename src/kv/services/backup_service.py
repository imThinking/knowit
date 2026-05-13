"""Backup and restore service for KnowIt database"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class BackupService:
    """Database backup and restore service"""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize backup service

        Args:
            data_dir: Data directory containing the database
        """
        from kv.core.config import config

        self.data_dir = data_dir or config.data_dir
        self.db_path = config.db_path
        self.backup_dir = config.home_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Path:
        """
        Create a database backup

        Args:
            name: Optional backup name
            description: Optional backup description

        Returns:
            Path to backup file
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if name:
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)
            backup_name = f"{timestamp}_{safe_name}.db"
        else:
            backup_name = f"{timestamp}.db"

        backup_path = self.backup_dir / backup_name

        # Copy database file
        shutil.copy2(self.db_path, backup_path)

        # Save metadata
        if description:
            metadata_path = self.backup_dir / f"{backup_name}.meta"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(f"timestamp: {timestamp}\n")
                f.write(f"name: {name or ''}\n")
                f.write(f"description: {description}\n")
                f.write(f"created_at: {datetime.now().isoformat()}\n")

        return backup_path

    def list_backups(self) -> List[dict]:
        """
        List all backups

        Returns:
            List of backup info dicts
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.db"):
            # Skip metadata files
            if backup_file.suffix == ".meta":
                continue

            stat = backup_file.stat()
            backup_info = {
                "path": str(backup_file),
                "name": backup_file.stem,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
            }

            # Try to read metadata
            metadata_path = self.backup_dir / f"{backup_file.name}.meta"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if ':' in line:
                                key, value = line.strip().split(':', 1)
                                backup_info[key.strip()] = value.strip()
                except Exception:
                    pass

            backups.append(backup_info)

        # Sort by creation time descending
        backups.sort(key=lambda x: x["created"], reverse=True)

        return backups

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")

        if not backup_file.suffix == '.db':
            raise ValueError(f"不是有效的数据库文件: {backup_path}")

        # Create backup of current database before restoring
        if self.db_path.exists():
            pre_restore_backup = self.create_backup(
                name="pre_restore",
                description="自动备份：恢复前"
            )
            click.echo(f"已创建当前数据库备份: {pre_restore_backup.name}")

        # Copy backup to database location
        shutil.copy2(backup_file, self.db_path)

        return True

    def delete_backup(self, backup_name: str) -> bool:
        """
        Delete a backup

        Args:
            backup_name: Backup filename

        Returns:
            True if successful
        """
        backup_file = self.backup_dir / backup_name

        if not backup_file.exists():
            return False

        # Delete backup and metadata
        backup_file.unlink()

        metadata_file = self.backup_dir / f"{backup_name}.meta"
        if metadata_file.exists():
            metadata_file.unlink()

        return True

    def clean_old_backups(
        self,
        keep_count: int = 10,
        dry_run: bool = False
    ) -> List[Path]:
        """
        Clean old backups, keeping only the most recent ones

        Args:
            keep_count: Number of backups to keep
            dry_run: If True, only report what would be deleted

        Returns:
            List of backup files that were (or would be) deleted
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return []

        # Delete old backups
        deleted = []

        for backup_info in backups[keep_count:]:
            backup_file = Path(backup_info["path"])

            if not dry_run:
                self.delete_backup(backup_file.name)

            deleted.append(backup_file)

        return deleted


# Global backup service instance
backup_service = BackupService()
