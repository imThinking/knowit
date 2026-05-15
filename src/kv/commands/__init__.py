"""KnowIt CLI commands

This module exports all CLI commands organized by functionality.
"""

from kv.commands.add import add
from kv.commands.search import search
from kv.commands.list_cmd import list_cmd
from kv.commands.export import export
from kv.commands.item import show, status, tag, merge, similar, delete, import_cmd
from kv.commands.collection import collection, collections
from kv.commands.tag import tags
from kv.commands.config import config
from kv.commands.system import stats, backup, export_cmd

__all__ = [
    # Core commands
    "add",
    "search",
    "list_cmd",
    "export",
    # Item management
    "show",
    "status",
    "tag",
    "merge",
    "similar",
    "delete",
    "import_cmd",
    # Collection management
    "collection",
    "collections",
    # Tag management
    "tags",
    # Configuration
    "config",
    # System
    "stats",
    "backup",
    "export_cmd",
]
