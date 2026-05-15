"""Tag management commands"""

import click

from kv.services.database import db
from kv.core.exceptions import DuplicateTagError, TagNotFoundError


@click.group()
def tags():
    """标签管理"""
    pass


@tags.command("list")
@click.option("--sort", "-s", default="name", type=click.Choice(["name", "count"]), help="排序方式")
def tags_list(sort: str):
    """列出所有标签

    示例：
        kv tags list
        kv tags list --sort count
    """
    all_tags = db.get_tags()

    if not all_tags:
        click.echo("还没有任何标签")
        return

    if sort == "count":
        all_tags.sort(key=lambda t: t.use_count, reverse=True)
    else:
        all_tags.sort(key=lambda t: t.name)

    click.echo(f"\n共有 {len(all_tags)} 个标签:\n")

    for tag in all_tags:
        click.echo(f"#{tag.name} ({tag.use_count} 使用)")


@tags.command("items")
@click.argument("tag_name")
@click.option("--limit", "-l", default=20, help="最大结果数")
def tags_items(tag_name: str, limit: int):
    """显示带有某标签的所有条目

    示例：
        kv tags items "Python"
        kv tags items "机器学习" --limit 50
    """
    tag = db.find_tag_by_name(tag_name)
    if not tag:
        click.echo(f"错误: 未找到标签: {tag_name}", err=True)
        return

    # Get all items and filter by tag
    all_items = db.get_items(limit=limit * 2)  # Get more to filter
    items_with_tag = []

    for item in all_items:
        item_tags = db.get_item_tags(item.id)
        if tag in item_tags:
            items_with_tag.append(item)

    items_with_tag = items_with_tag[:limit]

    if not items_with_tag:
        click.echo(f"没有使用标签 '#{tag_name}' 的条目")
        return

    click.echo(f"\n使用标签 '#{tag_name}' 的条目 ({len(items_with_tag)} 项):\n")

    for i, item in enumerate(items_with_tag, 1):
        status_icon = {"inbox": "📥", "archived": "📦", "starred": "⭐"}.get(item.status, "📄")
        click.echo(f"{i}. {status_icon} {item.title}")
        click.echo(f"   ID: {item.id}")
        click.echo()


@tags.command("rename")
@click.argument("old_name")
@click.argument("new_name")
def tags_rename(old_name: str, new_name: str):
    """重命名标签

    示例：
        kv tags rename "Python" "Python编程"
    """
    tag = db.find_tag_by_name(old_name)
    if not tag:
        click.echo(f"错误: 未找到标签: {old_name}", err=True)
        return

    try:
        db.update_tag(tag.id, name=new_name)
        click.echo(f"✓ 已将标签 '{old_name}' 重命名为 '{new_name}'")
    except DuplicateTagError:
        click.echo(f"错误: 标签已存在: {new_name}", err=True)


@tags.command("delete")
@click.argument("tag_name")
def tags_delete(tag_name: str):
    """删除标签

    示例：
        kv tags delete "旧标签"
    """
    tag = db.find_tag_by_name(tag_name)
    if not tag:
        click.echo(f"错误: 未找到标签: {tag_name}", err=True)
        return

    if not click.confirm(f"确认删除标签 '{tag_name}'? 这将从所有条目中移除该标签。"):
        return

    if db.delete_tag(tag.id):
        click.echo(f"✓ 已删除标签 '{tag_name}'")
    else:
        click.echo("错误: 删除失败", err=True)
