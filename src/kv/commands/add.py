"""Add command - Add web pages to knowledge base"""

import sys
import click

from kv.services.database import db
from kv.services.scraper import WebScraper, generate_simhash
from kv.algorithms.dedup import dedup
from kv.services.auto_export import auto_export_service
from kv.services.export_manager import export_manager
from kv.core.exceptions import (
    InvalidURLError,
    NetworkError,
    TimeoutError,
    ContentExtractionError,
)


@click.command()
@click.argument("url")
@click.option("--title", "-t", help="自定义标题")
@click.option("--author", "-a", help="作者")
@click.option("--collection", "-c", help="合集名称")
@click.option("--no-dedup", is_flag=True, help="跳过重复检测")
@click.option("--no-export", is_flag=True, help="跳过自动导出")
def add(url: str, title: str, author: str, collection: str, no_dedup: bool, no_export: bool):
    """添加网页到知识库

    示例：
        kv add https://example.com/article
        kv add https://example.com/article -t "我的标题"
    """
    scraper = WebScraper()

    # Validate URL
    if not scraper.validate_url(url):
        click.echo(f"错误: 无效的 URL: {url}", err=True)
        sys.exit(1)

    # Check if already exists
    existing = db.find_by_url(url)
    if existing:
        click.echo(f"该 URL 已存在于知识库中: {existing.title} (ID: {existing.id})")
        sys.exit(0)

    try:
        # Fetch content
        with click.progressbar(length=100, label="正在抓取内容") as bar:
            bar.update(50)
            content = scraper.fetch(url)
            bar.update(100)

        # Use custom values if provided
        final_title = title or content.title
        final_author = author or content.author

        # Compute simhash
        simhash = generate_simhash(content.content_text)

        # Check for duplicates
        if not no_dedup:
            with click.progressbar(length=100, label="正在检测重复") as bar:
                bar.update(100)
            duplicates = dedup.find_duplicates(content.content_text)

            if duplicates:
                click.echo(f"\n发现 {len(duplicates)} 个相似内容:")
                for item, similarity in duplicates[:5]:
                    click.echo(
                        f"  - {item.title} (相似度: {similarity:.1%}) "
                        f"[{item.source_type}]"
                    )

                best_match = duplicates[0]
                if best_match[1] > 0.9:
                    # Very high similarity - likely a duplicate
                    if click.confirm("\n内容高度相似，是否跳过添加？"):
                        click.echo("已跳过添加")
                        sys.exit(0)

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
            source_type="webpage",
            source_url=url,
            author=final_author,
            content_html=content.content_html,
            content_text=content.content_text,
            word_count=content.word_count,
            reading_time=content.reading_time,
            collection_id=collection_id,
            simhash=simhash,
        )

        click.echo(f"✓ 已添加: {final_title}")
        click.echo(f"  ID: {item.id}")
        click.echo(f"  字数: {content.word_count:,} | 预计阅读时间: {content.reading_time} 分钟")

        # Auto export
        if not no_export:
            try:
                export_path = auto_export_service.export_item(item.id)
                if export_path:
                    relative_path = export_path.relative_to(export_manager.get_export_root())
                    click.echo(f"  已导出: {relative_path}")
            except Exception as e:
                click.echo(f"  警告: 自动导出失败 - {e}")

    except InvalidURLError as e:
        click.echo(f"错误: {e.message}", err=True)
        sys.exit(1)
    except (NetworkError, TimeoutError) as e:
        click.echo(f"网络错误: {e.message}", err=True)
        sys.exit(1)
    except ContentExtractionError as e:
        click.echo(f"内容提取失败: {e.message}", err=True)
        sys.exit(1)
