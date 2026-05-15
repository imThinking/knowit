"""Configuration management commands"""

import sys
import os
import click

from kv.services.config_service import config_service
from kv.core.exceptions import ConfigurationError


@click.group()
def config():
    """配置管理"""
    pass


@config.command("init")
def config_init():
    """初始化配置文件"""
    try:
        config_service.init_config()
        click.echo(f"✓ 配置文件已创建: {config_service.config_file}")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """获取配置值

    示例：
        kv config get similarity_threshold
        kv config get meilisearch_url
    """
    try:
        value = config_service.get(key)
        if value is None:
            click.echo(f"配置项不存在: {key}")
        else:
            click.echo(f"{key} = {value}")
    except ConfigurationError as e:
        click.echo(f"错误: {e.message}", err=True)
        sys.exit(1)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置配置值

    示例：
        kv config set similarity_threshold 0.8
        kv config set meilisearch_url http://localhost:7700
    """
    try:
        # Try to convert value to appropriate type
        try:
            value = float(value)
            if value == int(value):
                value = int(value)
        except ValueError:
            pass

        config_service.set(key, value)
        click.echo(f"✓ 已设置: {key} = {value}")
    except ConfigurationError as e:
        click.echo(f"错误: {e.message}", err=True)
        sys.exit(1)


@config.command("list")
def config_list():
    """列出所有配置"""
    config_dict = config_service.get_all()

    if not config_dict:
        click.echo("配置为空")
        return

    click.echo("\n当前配置:\n")
    _print_config_dict(config_dict)
    click.echo()


@config.command("edit")
def config_edit():
    """编辑配置文件"""
    import subprocess

    config_file = config_service.config_file

    if not config_file.exists():
        click.echo(f"配置文件不存在，请先运行 'kv config init'")
        return

    # Open in default editor
    try:
        if sys.platform == "win32":
            os.startfile(str(config_file))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(config_file)])
        else:
            subprocess.run(["xdg-open", str(config_file)])
        click.echo(f"已打开配置文件: {config_file}")
    except Exception as e:
        click.echo(f"无法打开编辑器: {e}", err=True)


def _print_config_dict(d: dict, indent: int = 0):
    """Helper to print config dict with indentation"""
    for key, value in d.items():
        prefix = "  " * indent
        if isinstance(value, dict):
            click.echo(f"{prefix}{key}:")
            _print_config_dict(value, indent + 1)
        else:
            click.echo(f"{prefix}{key}: {value}")
