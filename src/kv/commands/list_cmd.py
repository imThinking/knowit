"""List command - List items in knowledge base"""

import click

from kv.services.database import db


@click.command()
@click.option("--status", "-s", default="inbox", help="状态筛选", type=click.Choice(["inbox", "archived", "starred", "merged", "all"]))
@click.option("--collection", "-c", help="合集筛选")
@click.option("--limit", "-l", default=20, help="最大显示数量")
def list_cmd(status: str, collection: str, limit: int):
    """列出知识库内容

    示例：
        kv list
        kv list -s archived -l 50
        kv list -c "Python"
    """
    collection_id = None
    if collection:
        coll = db.get_collection_by_name(collection)
        if not coll:
            click.echo(f"错误: 未找到合集: {collection}", err=True)
            return
        collection_id = coll.id

    items = db.get_items(
        status=None if status == "all" else status,
        collection_id=collection_id,
        limit=limit
    )

    if not items:
        click.echo(f"没有找到{status}状态的内容")
        return

    status_name = {
        "inbox": "收件箱",
        "archived": "已归档",
        "starred": "已标星",
        "merged": "已合并",
        "all": "所有"
    }.get(status, status)

    click.echo(f"\n{status_name}内容 ({len(items)} 项):\n")

    for i, item in enumerate(items, 1):
        click.echo(f"{i}. {item.title}")

        if item.author:
            click.echo(f"   作者: {item.author}")

        if item.word_count:
            click.echo(f"   字数: {item.word_count:,} | 阅读时间: {item.reading_time} 分钟")

        if item.source_url:
            click.echo(f"   来源: {item.source_url}")

        # Show collection
        if item.collection_id:
            coll = db.get_collection(item.collection_id)
            if coll:
                click.echo(f"   合集: {coll.name}")

        # Show tags
        item_tags = db.get_item_tags(item.id)
        if item_tags:
            tag_names = [f"#{t.name}" for t in item_tags]
            click.echo(f"   标签: {' '.join(tag_names)}")

        click.echo(f"   创建于: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"   ID: {item.id}")
        click.echo()
