"""Collection management commands"""

import click

from kv.services.database import db
from kv.core.exceptions import DuplicateCollectionError, CollectionNotFoundError


@click.command()
@click.argument("name")
@click.option("--description", "-d", help="合集描述")
def collection(name: str, description: str):
    """创建新合集

    示例：
        kv collection "Python 编程" -d "Python 相关文章"
    """
    try:
        coll = db.create_collection(name=name, description=description)
        click.echo(f"✓ 创建合集: {coll.name} (ID: {coll.id})")
    except DuplicateCollectionError:
        click.echo(f"错误: 合集已存在: {name}", err=True)


@click.command()
def collections():
    """列出所有合集

    示例：
        kv collections
    """
    collections_list = db.get_collections()

    if not collections_list:
        click.echo("还没有任何合集")
        return

    click.echo(f"\n共有 {len(collections_list)} 个合集:\n")

    for coll in collections_list:
        click.echo(f"📁 {coll.name}")
        if coll.description:
            click.echo(f"   描述: {coll.description}")
        click.echo(f"   条目数: {coll.item_count}")
        click.echo(f"   ID: {coll.id}")

        # Show child collections
        children = db.get_collections(parent_id=coll.id)
        if children:
            child_names = [c.name for c in children]
            click.echo(f"   子合集: {', '.join(child_names)}")

        click.echo()
