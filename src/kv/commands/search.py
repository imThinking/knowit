"""Search command - Search knowledge base"""

import click

from kv.services.database import db


@click.command()
@click.argument("query", required=False)
@click.option("--limit", "-l", default=20, help="最大结果数")
@click.option("--status", "-s", help="按状态筛选", type=click.Choice(["inbox", "archived", "starred"]))
@click.option("--tag", "-t", help="按标签筛选")
@click.option("--collection", "-c", help="按合集筛选")
@click.option("--url", is_flag=True, help="只显示 URL")
def search(query: str, limit: int, status: str, tag: str, collection: str, url: bool):
    """搜索知识库

    示例：
        kv search "机器学习"
        kv search -s archived -l 50
        kv search --tag "Python"
    """
    if not query:
        # Show all items matching filters
        items = db.get_items(status=status, collection_id=collection, limit=limit)
    else:
        # Search by query
        items = db.search_items(query, limit=limit)

        # Apply additional filters
        if status:
            items = [i for i in items if i.status == status]
        if collection:
            items = [i for i in items if i.collection_id == collection]

    # Filter by tag if specified
    if tag:
        filtered_items = []
        for item in items:
            item_tags = db.get_item_tags(item)
            tag_names = [t.name for t in item_tags]
            if tag in tag_names:
                filtered_items.append(item)
        items = filtered_items

    if not items:
        if query:
            click.echo(f"未找到匹配 '{query}' 的内容")
        else:
            click.echo("没有找到任何内容")
        return

    click.echo(f"找到 {len(items)} 个结果:\n")

    for i, item in enumerate(items, 1):
        if url:
            click.echo(f"{item.source_url}")
        else:
            status_icon = {"inbox": "📥", "archived": "📦", "starred": "⭐"}.get(item.status, "📄")
            click.echo(f"{i}. {status_icon} {item.title}")

            if item.author:
                click.echo(f"   作者: {item.author}")

            if item.word_count:
                click.echo(f"   字数: {item.word_count:,}")

            if item.source_url:
                click.echo(f"   来源: {item.source_url}")

            # Show tags
            item_tags = db.get_item_tags(item.id)
            if item_tags:
                tag_names = [t.name for t in item_tags]
                click.echo(f"   标签: {', '.join(tag_names)}")

            click.echo(f"   ID: {item.id}")
            click.echo()
