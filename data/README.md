# KnowIt Data Directory

This directory stores KnowIt database files.

## Files

- `vault.db` - Main SQLite database (created automatically on first use)
- `vault.db-journal` - SQLite journal file (temporary, during writes)

## Database

The database is automatically initialized when you:
- Add your first item with `kv add`
- Run `kv status`

## Backup

Regular backups are recommended:
```bash
# Backup to timestamped file
kv backup create

# List all backups
kv backup list

# Restore from backup
kv backup restore <backup-file>
```

## Database Schema

The database contains the following tables:
- `items` - Knowledge entries (articles, notes, etc.)
- `collections` - Hierarchical collections for organizing items
- `tags` - Tags for categorizing items
- `item_tags` - Many-to-many relationship between items and tags
- `item_similarity` - Cached similarity scores between items
