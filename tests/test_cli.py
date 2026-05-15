"""Tests for CLI commands

Uses Click's CliRunner for testing CLI commands.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile

from kv.cli import cli


class TestCLICommands:
    """Test basic CLI commands"""

    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'KnowIt' in result.output
        assert 'add' in result.output
        assert 'search' in result.output
        assert 'list' in result.output

    def test_version(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert '0.1.0' in result.output


class TestAddCommand:
    """Test add command"""

    def test_add_invalid_url(self, cli_runner):
        """Test adding with invalid URL"""
        result = cli_runner.invoke(cli, ['add', 'not-a-url'])

        assert result.exit_code != 0
        assert '无效' in result.output or 'invalid' in result.output.lower()

    @pytest.mark.integration
    def test_add_valid_url(self, cli_runner):
        """Test adding with valid URL (integration test)"""
        # This would make a real network request
        # Skip in unit tests
        pass


class TestListCommand:
    """Test list command"""

    def test_list_default(self, cli_runner, temp_db, sample_item):
        """Test listing items with default options"""
        result = cli_runner.invoke(cli, ['list'])

        assert result.exit_code == 0
        # Output should contain items or message about no items

    def test_list_with_status(self, cli_runner, temp_db):
        """Test listing items with status filter"""
        # Create items with different statuses
        temp_db.create_item(title="Inbox", source_type="webpage", status="inbox")
        temp_db.create_item(title="Archived", source_type="webpage", status="archived")

        result = cli_runner.invoke(cli, ['list', '--status', 'inbox'])

        assert result.exit_code == 0

    def test_list_with_collection(self, cli_runner, temp_db, sample_collection):
        """Test listing items with collection filter"""
        result = cli_runner.invoke(cli, ['list', '--collection', sample_collection.name])

        assert result.exit_code == 0


class TestSearchCommand:
    """Test search command"""

    def test_search_no_query(self, cli_runner, temp_db, sample_item):
        """Test search without query (lists all)"""
        result = cli_runner.invoke(cli, ['search'])

        assert result.exit_code == 0

    def test_search_with_query(self, cli_runner, temp_db):
        """Test search with query"""
        temp_db.create_item(
            title="Python Programming",
            source_type="webpage",
            content_text="Learn Python programming"
        )

        result = cli_runner.invoke(cli, ['search', 'Python'])

        assert result.exit_code == 0
        # Should find Python-related content


class TestCollectionCommands:
    """Test collection management commands"""

    def test_collection_create(self, cli_runner):
        """Test creating a collection"""
        result = cli_runner.invoke(cli, ['collection', 'Test Collection'])

        assert result.exit_code == 0
        assert 'Test Collection' in result.output

    def test_collections_list(self, cli_runner, temp_db, sample_collection):
        """Test listing collections"""
        result = cli_runner.invoke(cli, ['collections'])

        assert result.exit_code == 0
        # Should show collections


class TestTagCommands:
    """Test tag management commands"""

    def test_tags_list(self, cli_runner, temp_db, sample_tag):
        """Test listing tags"""
        result = cli_runner.invoke(cli, ['tags', 'list'])

        assert result.exit_code == 0
        # Should show tags

    def test_tag_item(self, cli_runner, temp_db, sample_item):
        """Test adding tag to item"""
        result = cli_runner.invoke(cli, ['tag', sample_item.id, '--tag', 'test-tag'])

        assert result.exit_code == 0
        # Should confirm tag added


class TestExportCommands:
    """Test export commands"""

    def test_export_invalid_item(self, cli_runner):
        """Test exporting non-existent item"""
        result = cli_runner.invoke(cli, ['export', 'non-existent-id'])

        assert result.exit_code != 0
        assert '未找到' in result.output or 'not found' in result.output.lower()

    def test_export_list(self, cli_runner):
        """Test listing exports"""
        result = cli_runner.invoke(cli, ['exports', 'list'])

        assert result.exit_code == 0


class TestConfigCommands:
    """Test configuration commands"""

    def test_config_get(self, cli_runner):
        """Test getting config value"""
        result = cli_runner.invoke(cli, ['config', 'get', 'similarity_threshold'])

        assert result.exit_code == 0

    def test_config_list(self, cli_runner):
        """Test listing all config"""
        result = cli_runner.invoke(cli, ['config', 'list'])

        assert result.exit_code == 0


class TestSystemCommands:
    """Test system commands"""

    def test_stats(self, cli_runner):
        """Test stats command"""
        result = cli_runner.invoke(cli, ['stats'])

        assert result.exit_code == 0
        assert '统计' in result.output or 'stats' in result.output.lower()

    def test_backup_list(self, cli_runner):
        """Test listing backups"""
        result = cli_runner.invoke(cli, ['backup', 'list'])

        assert result.exit_code == 0
