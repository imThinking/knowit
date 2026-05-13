# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KnowIt is a personal knowledge base CLI tool for collecting, organizing, and searching web content. It features intelligent content deduplication using simhash, full-text search via Meilisearch, and PDF export using the Kami design system.

**Language**: The README and documentation are in Chinese. This is intentional for the target audience. Code comments and variable names should remain in English for maintainability.

## Architecture

### Module Structure

```
src/kv/
├── cli.py              # Click-based CLI entry point (kv command)
├── core/
│   ├── config.py       # Config class managing paths and settings
│   └── database.py     # SQLAlchemy ORM models
├── services/           # Business logic layer (planned)
├── algorithms/         # Similarity detection, clustering (planned)
└── utils/              # Helper functions (planned)
```

### Database Models (SQLAlchemy + SQLite)

Located in `src/kv/core/database.py`:

- **Item**: Knowledge entries with content in HTML/Markdown/text, simhash for deduplication
- **Collection**: Hierarchical collections for organizing items
- **Tag**: Tagging system with colors
- **ItemTag**: Many-to-many relationship between items and tags
- **ItemSimilarity**: Cached similarity scores between items

Key relationships:
- `Item.collection_id` → `Collection.id` (foreign key)
- `Item.merged_into` → `Item.id` (self-referential for duplicate handling)
- `Item.simhash` - used for near-duplicate detection

### Configuration

The `Config` class (`src/kv/core/config.py`) manages:
- Base directory via `KNOWIT_HOME` env var (default: `~/KnowIt`)
- Subdirectories: `data/`, `config/`, `logs/`
- Database path: `$KNOWIT_HOME/data/vault.db`
- Meilisearch URL via `KNOWIT_MEILISEARCH_URL` (default: `http://localhost:7700`)
- Similarity threshold: 0.75 (default)

## Development Commands

### Initial Setup

```bash
# Windows (PowerShell)
.\setup.bat

# Manual setup
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -e .
python scripts/init_db.py
```

### Daily Development

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate  # Linux/Mac

# Run CLI
kv --help
kv add https://example.com
kv search "query"

# Run tests
pytest tests/

# Linting and formatting
black src/ tests/
ruff check src/ tests/
mypy src/
```

### Test Environment

```bash
python scripts/test_setup.py  # Test imports, database, CLI
```

## Key Dependencies

- **click**: CLI framework
- **sqlalchemy**: ORM for SQLite database
- **beautifulsoup4** + **lxml**: HTML parsing
- **simhash**: Near-duplicate detection using simhash algorithm
- **jieba**: Chinese text segmentation
- **scikit-learn**: Clustering algorithms
- **weasyprint**: PDF generation
- **playwright**: Browser automation for web scraping

## Windows-Specific Notes

This project is actively developed on Windows. Key considerations:
- Virtual environment activation uses `.\venv\Scripts\Activate.ps1`
- PowerShell execution policy may need: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Scripts use `.bat` extensions for setup

## Project Status

Alpha (v0.1.0). Core features implemented:
- Database service layer with full CRUD operations
- Web scraping service using requests + BeautifulSoup
- Simhash-based deduplication algorithm
- CLI commands: `add`, `search`, `list`, `collection`, `collections`, `tag`, `status`
- URL deduplication (prevents adding duplicate URLs)
- Automatic simhash computation and similarity detection

Partially implemented:
- `export` command (framework exists, PDF generation using WeasyPrint not yet implemented)
- Tag system (basic operations work)

Not yet implemented:
- Meilisearch integration (using SQLite LIKE for now)
- PDF export with Kami design system
- Playwright-based dynamic content scraping
- Advanced clustering algorithms
