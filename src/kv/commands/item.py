"""Item management commands - Show, delete, status, merge, similar, import"""

import sys
import click
from pathlib import Path

from kv.services.database import db
from kv.services.scraper import scrape_file
from kv.algorithms.dedup import dedup
from kv.core.exceptions import ItemNotFoundError, FileReadError


@click.command()
@click.argument("item_id")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "json", "html"]), help="输出格式")
def show(item_id: str, format: str):
    """显示条目详情

    示例：
        kv show <item_id>
        kv show <item_id> --format json
    """
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目: {item_id}", err=True)
        return

    if format == "json":
        import json
        data = {
            "id": item.id,
            "title": item.title,
            "author": item.author,
            "source_type": item.source_type,
            "source_url": item.source_url,
            "word_count": item.word_count,
            "reading_time": item.reading_time,
            "status": item.status,
            "collection_id": item.collection_id,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif format == "html":
        click.echo(item.content_html or item.content_text or "")
    else:
        # Text format
        click.echo(f"标题: {item.title}")
        if item.author:
            click.echo(f"作者: {item.author}")
        if item.source_url:
            click.echo(f"来源: {item.source_url}")
        click.echo(f"类型: {item.source_type}")
        click.echo(f"状态: {item.status}")
        if item.word_count:
            click.echo(f"字数: {item.word_count:,} | 阅读时间: {item.reading_time} 分钟")
        click.echo(f"创建于: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"ID: {item.id}")

        # Collection
        if item.collection_id:
            coll = db.get_collection(item.collection_id)
            if coll:
                click.echo(f"合集: {coll.name}")

        # Tags
        tags = db.get_item_tags(item.id)
        if tags:
            tag_names = [t.name for t in tags]
            click.echo(f"标签: {', '.join(tag_names)}")

        click.echo("\n" + "="*60)
        click.echo(item.content_text or "")


@click.command()
@click.argument("item_id")
@click.argument("new_status", type=click.Choice(["inbox", "archived", "starred", "merged"]))
@click.option("--undo", is_flag=True, help="撤销到 inbox")
def status(item_id: str, new_status: str, undo: bool):
    """更改条目状态

    示例：
        kv status <item_id> archived
        kv status <item_id> starred --undo
    """
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目: {item_id}", err=True)
        return

    if undo:
        new_status = "inbox"

    db.update_item(item_id, status=new_status)
    click.echo(f"✓ 已将 '{item.title}' 状态更改为 {new_status}")


@click.command()
@click.argument("item_id")
@click.option("--tag", "-t", required=True, help="标签名称")
def tag(item_id: str, tag: str):
    """为条目添加标签

    示例：
        kv tag <item_id> -t "Python"
        kv tag <item_id> -t "机器学习"
    """
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目: {item_id}", err=True)
        return

    tag_obj = db.add_tag_to_item(item_id, tag)
    click.echo(f"✓ 已为 '{item.title}' 添加标签: {tag_obj.name}")


@click.command()
@click.argument("source_id")
@click.argument("target_id")
@click.option("--keep-both", is_flag=True, help="保留两个条目但链接它们")
def merge(source_id: str, target_id: str, keep_both: bool):
    """合并两个相似条目

    示例：
        kv merge <source_id> <target_id>
        kv merge <source_id> <target_id> --keep-both
    """
    source = db.get_item(source_id)
    target = db.get_item(target_id)

    if not source or not target:
        click.echo("错误: 未找到一个或两个条目", err=True)
        return

    click.echo(f"合并:")
    click.echo(f"  源: {source.title} ({source_id})")
    click.echo(f"  目标: {target.title} ({target_id})")

    if not click.confirm("\n确认合并?"):
        return

    try:
        result = dedup.merge_items(source_id, target_id, keep_both=keep_both)
        if keep_both:
            click.echo(f"✓ 已链接条目")
        else:
            click.echo(f"✓ 已合并条目到 '{result.title}'")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)


@click.command()
@click.argument("item_id")
@click.option("--threshold", "-t", default=0.75, type=float, help="相似度阈值")
@click.option("--limit", "-l", default=10, help="最大结果数")
def similar(item_id: str, threshold: float, limit: int):
    """查找相似条目

    示例：
        kv similar <item_id>
        kv similar <item_id> --threshold 0.8 --limit 20
    """
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目: {item_id}", err=True)
        return

    results = db.get_similar_items(item_id, threshold=threshold)

    if not results:
        click.echo(f"未找到相似条目 (阈值: {threshold})")
        return

    # Limit results
    results = results[:limit]

    click.echo(f"找到 {len(results)} 个相似条目 (阈值: {threshold}):\n")

    for i, (similar_item, similarity) in enumerate(results, 1):
        click.echo(f"{i}. {similar_item.title}")
        click.echo(f"   相似度: {similarity:.1%}")
        click.echo(f"   ID: {similar_item.id}")
        click.echo()


@click.command()
@click.argument("item_id")
def delete(item_id: str):
    """删除条目

    示例：
        kv delete <item_id>
    """
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目: {item_id}", err=True)
        return

    click.echo(f"删除: {item.title}")
    click.echo(f"  ID: {item_id}")

    if not click.confirm("\n确认删除?"):
        return

    if db.delete_item(item_id):
        click.echo("✓ 已删除条目")
    else:
        click.echo("错误: 删除失败", err=True)


@click.command("import")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--title", "-t", help="自定义标题")
@click.option("--author", "-a", help="作者")
@click.option("--collection", "-c", help="合集名称")
def import_cmd(file_path: str, title: str, author: str, collection: str):
    """导入本地文件到知识库

    支持格式: HTML, Markdown, TXT

    示例：
        kv import document.html
        kv import article.md -t "我的标题"
    """
    try:
        content = scrape_file(file_path)
    except FileReadError as e:
        click.echo(f"错误: {e.message}", err=True)
        return

    final_title = title or content.title
    final_author = author or content.author

    # Find or create collection
    collection_id = None
    if collection:
        coll = db.get_collection_by_name(collection)
        if not coll:
            coll = db.create_collection(name=collection)
            click.echo(f"创建合集: {collection}")
        collection_id = coll.id

    # Create item
    item = db.create_item(
        title=final_title,
        source_type="local",
        source_url=str(Path(file_path).absolute()),
        author=final_author,
        content_html=content.content_html,
        content_text=content.content_text,
        word_count=content.word_count,
        reading_time=content.reading_time,
        collection_id=collection_id,
    )

    click.echo(f"✓ 已导入: {final_title}")
    click.echo(f"  ID: {item.id}")
    click.echo(f"  字数: {content.word_count:,} | 阅读时间: {content.reading_time} 分钟")
