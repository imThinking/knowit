"""KnowIt CLI 命令行接口"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional

import click

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from kv.services.database import db
from kv.services.scraper import WebScraper, generate_simhash
from kv.services.pdf_export import html_exporter
from kv.services.config_service import config_service
from kv.services.export_manager import export_manager
from kv.services.backup_service import backup_service
from kv.algorithms.dedup import dedup


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """KnowIt - 你的第二大脑，优雅地归集网络碎片。"""
    pass


@cli.command()
@click.argument("url")
@click.option("--title", "-t", help="自定义标题")
@click.option("--author", "-a", help="作者")
@click.option("--collection", "-c", help="合集名称")
@click.option("--no-dedup", is_flag=True, help="跳过重复检测")
def add(url: str, title: Optional[str], author: Optional[str], collection: Optional[str], no_dedup: bool):
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
                coll = db.create_collection(collection)
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
            content_markdown=None,  # Can be added later
            word_count=content.word_count,
            reading_time=content.reading_time,
            collection_id=collection_id,
            simhash=simhash,
        )

        click.echo(f"\n[OK] 成功添加: {item.title}")
        click.echo(f"  ID: {item.id}")
        click.echo(f"  字数: {content.word_count}")
        click.echo(f"  阅读时间: {content.reading_time} 分钟")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query", required=False)
@click.option("--limit", "-l", default=20, help="最大结果数")
@click.option("--status", "-s", help="按状态筛选 (inbox/archived/starred)")
@click.option("--tag", "-t", help="按标签筛选")
@click.option("--collection", "-c", help="按合集筛选")
@click.option("--author", "-a", help="按作者筛选")
@click.option("--after", help="日期之后 (YYYY-MM-DD)")
@click.option("--before", help="日期之前 (YYYY-MM-DD)")
@click.option("--format", "-f", type=click.Choice(['list', 'table']), default='list', help="输出格式")
def search(query: Optional[str], limit: int, status: Optional[str], tag: Optional[str],
           collection: Optional[str], author: Optional[str], after: Optional[str],
           before: Optional[str], format: str):
    """搜索知识库（支持多条件过滤）

    示例：
        kv search "Python"
        kv search -s archived
        kv search -t "机器学习"
        kv search -c "Python学习"
        kv search --after 2026-01-01
        kv search -a "作者名"
        kv search "Python" -t "教程" -s starred
    """
    from datetime import datetime
    from kv.core.database import Item

    with db.get_session() as session:
        query_obj = session.query(Item).filter(Item.status != 'merged')

        # Apply filters
        if status:
            query_obj = query_obj.filter(Item.status == status)

        if collection:
            coll = db.get_collection_by_name(collection)
            if coll:
                query_obj = query_obj.filter(Item.collection_id == coll.id)
            else:
                click.echo(f"错误: 未找到合集 '{collection}'", err=True)
                sys.exit(1)

        if author:
            query_obj = query_obj.filter(Item.author.like(f'%{author}%'))

        if after:
            try:
                after_date = datetime.strptime(after, '%Y-%m-%d')
                query_obj = query_obj.filter(Item.created_at >= after_date)
            except ValueError:
                click.echo(f"错误: 日期格式错误，应为 YYYY-MM-DD", err=True)
                sys.exit(1)

        if before:
            try:
                before_date = datetime.strptime(before, '%Y-%m-%d')
                query_obj = query_obj.filter(Item.created_at <= before_date)
            except ValueError:
                click.echo(f"错误: 日期格式错误，应为 YYYY-MM-DD", err=True)
                sys.exit(1)

        # Text search
        if query:
            search_pattern = f"%{query}%"
            query_obj = query_obj.filter(
                (Item.title.like(search_pattern)) | (Item.content_text.like(search_pattern))
            )

        # Tag filtering (need to join)
        if tag:
            from kv.core.database import ItemTag, Tag
            tag_obj = db.find_tag_by_name(tag)
            if tag_obj:
                query_obj = query_obj.join(ItemTag).filter(ItemTag.tag_id == tag_obj.id)
            else:
                click.echo(f"未找到标签 '{tag}'")
                sys.exit(0)

        # Execute query
        results = query_obj.order_by(Item.created_at.desc()).limit(limit).all()

    if not results:
        filter_desc = []
        if query: filter_desc.append(f"搜索'{query}'")
        if status: filter_desc.append(f"状态={status}")
        if tag: filter_desc.append(f"标签={tag}")
        if collection: filter_desc.append(f"合集={collection}")
        if author: filter_desc.append(f"作者={author}")
        if after: filter_desc.append(f"日期>{after}")
        if before: filter_desc.append(f"日期<{before}")

        filter_str = " & ".join(filter_desc) if filter_desc else "所有条目"
        click.echo(f"未找到匹配的结果: {filter_str}")
        sys.exit(0)

    click.echo(f"找到 {len(results)} 个结果\n")

    if format == 'table':
        # Table format
        click.echo(f"{'标题':<50} {'来源':<30} {'作者':<15} {'状态':<10}")
        click.echo("-" * 105)
        for item in results:
            title = item.title[:47] + "..." if len(item.title) > 50 else item.title
            source = item.source_url[:27] + "..." if item.source_url and len(item.source_url) > 30 else (item.source_url or "本地")
            author_str = item.author[:12] + "..." if item.author and len(item.author) > 15 else (item.author or "")
            click.echo(f"{title:<50} {source:<30} {author_str:<15} {item.status:<10}")
    else:
        # List format
        for i, item in enumerate(results, 1):
            status_emoji = {
                "inbox": "[Inbox]",
                "archived": "[Archived]",
                "starred": "[Starred]",
                "merged": "[Merged]",
            }.get(item.status, "[Item]")

            click.echo(f"{i}. {status_emoji} {item.title}")
            click.echo(f"   来源: {item.source_url or '本地'}")
            if item.author:
                click.echo(f"   作者: {item.author}")
            click.echo(f"   时间: {item.created_at.strftime('%Y-%m-%d %H:%M')}")

            # Show tags
            tags = db.get_item_tags(item.id)
            if tags:
                tag_names = [f"#{t.name}" for t in tags]
                click.echo(f"   标签: {' '.join(tag_names)}")

            click.echo(f"   ID: {item.id}")
            click.echo()


@cli.command()
@click.option("--status", "-s", default="inbox", help="按状态筛选")
@click.option("--collection", "-c", help="按合集筛选")
@click.option("--limit", "-l", default=20, help="最大结果数")
def list(status: str, collection: Optional[str], limit: int):
    """列出知识库中的条目

    示例：
        kv list
        kv list -s archived
        kv list -c "Python 学习"
    """
    collection_id = None
    if collection:
        coll = db.get_collection_by_name(collection)
        if not coll:
            click.echo(f"错误: 未找到合集 '{collection}'", err=True)
            sys.exit(1)
        collection_id = coll.id

    items = db.get_items(status=status, collection_id=collection_id, limit=limit)

    if not items:
        click.echo("没有找到任何条目")
        sys.exit(0)

    click.echo(f"共 {len(items)} 个条目:\n")

    for item in items:
        status_emoji = {
            "inbox": "[Inbox]",
            "archived": "[Archived]",
            "starred": "[Starred]",
            "merged": "[Merged]",
        }.get(item.status, "[Item]")

        click.echo(f"{status_emoji} {item.title}")
        click.echo(f"   来源: {item.source_url or '本地'}")
        click.echo(f"   创建时间: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"   ID: {item.id}")
        click.echo()


@cli.command()
@click.argument("item_id")
@click.option("--output", "-o", help="自定义输出路径（覆盖默认目录结构）")
@click.option("--format", "-f", type=click.Choice(['html', 'pdf', 'both']), default='html', help="输出格式")
@click.option("--open", is_flag=True, help="导出后自动打开")
@click.option("--print", is_flag=True, help="打开浏览器打印对话框")
@click.option("--organize-by", type=click.Choice(['date', 'collection', 'none']), help="目录组织方式")
@click.option("--simple", is_flag=True, help="使用简单格式（无封面页）")
@click.option("--kami", is_flag=True, help="使用 Kami 完整格式（带封面页）")
@click.option("--clean", is_flag=True, help="清理 HTML 内容（移除样式、脚本等）")
@click.option("--font-dir", help="Kami 字体目录路径（用于 PDF 生成）")
def export(item_id: str, output: Optional[str], format: str, open: bool, print: bool, organize_by: Optional[str], simple: bool, kami: bool, clean: bool, font_dir: Optional[str]):
    """导出条目为 HTML/PDF（Kami 设计系统）

    默认使用简单 HTML 格式。使用 --kami 添加封面页。
    使用 --format pdf 生成 PDF 文件（需要 WeasyPrint）。
    使用 --clean 清理 HTML 内容（推荐用于微信公众号文章）。
    默认按日期组织文件，导出到配置的导出目录。

    示例：
        kv export <item_id>                    # 简单 HTML 格式
        kv export <item_id> --kami              # Kami 完整格式（封面页）
        kv export <item_id> --format pdf        # 生成 PDF
        kv export <item_id> --format both       # 同时生成 HTML 和 PDF
        kv export <item_id> --clean             # 清理 HTML 内容
        kv export <item_id> --open              # 导出后自动打开
        kv export <item_id> -o custom.html
        kv export <item_id> --font-dir /path/to/fonts
    """
    item = db.get_item(item_id)

    if not item:
        click.echo(f"错误: 未找到 ID 为 {item_id} 的条目", err=True)
        sys.exit(1)

    try:
        click.echo(f"正在导出: {item.title}")

        # Use content_html if available, otherwise use content_text wrapped in <p>
        content = item.content_html or f"<p>{item.content_text}</p>"

        # Determine output path
        if output:
            # Custom output path specified
            output_path = Path(output)
        else:
            # Use organized directory structure
            organize_method = organize_by or config_service.get('export.organize_by', 'date')
            export_format = config_service.get('export.default_format', 'html')

            # Get collection name if organizing by collection
            collection_name = None
            if organize_method == 'collection' and item.collection_id:
                coll = db.get_collection(item.collection_id)
                collection_name = coll.name if coll else None

            # Get organized export path
            output_path = export_manager.get_export_path(
                item_title=item.title,
                item_date=item.created_at,
                collection_name=collection_name,
                export_format=export_format,
                organize_by=organize_method if organize_method != 'none' else None
            )

        # Generate outputs based on format
        generated_files = []

        if format in ['html', 'both']:
            # Generate HTML
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
                temp_path = Path(tmp.name)

            # Choose export method
            if kami:
                # Use Kami full format with cover page
                html_exporter.generate_html(
                    title=item.title,
                    content=content,
                    author=item.author,
                    url=item.source_url,
                    created_at=item.created_at,
                    output_path=str(temp_path),
                    clean=clean
                )
            else:
                # Use simple format (default)
                html_exporter.generate_html_simple(
                    title=item.title,
                    content=content,
                    author=item.author,
                    url=item.source_url,
                    created_at=item.created_at,
                    output_path=str(temp_path),
                    clean=clean
                )

            # Move to final location
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_path), str(output_path))
            generated_files.append(output_path)

        if format in ['pdf', 'both']:
            # Generate PDF
            pdf_path = output_path.with_suffix('.pdf') if output_path else None

            try:
                pdf_file = html_exporter.generate_pdf(
                    title=item.title,
                    content=content,
                    author=item.author,
                    url=item.source_url,
                    created_at=item.created_at,
                    output_path=str(pdf_path) if pdf_path else None,
                    clean=clean,
                    font_dir=font_dir
                )
                generated_files.append(Path(pdf_file))
            except Exception as e:
                click.echo(f"警告: PDF 生成失败: {e}", err=True)
                if format == 'pdf':
                    raise

        # Display results
        relative_path = export_manager.get_relative_path(generated_files[0]) if generated_files else ""

        click.echo(f"[OK] 已导出 {len(generated_files)} 个文件:")
        for i, file_path in enumerate(generated_files, 1):
            rel = export_manager.get_relative_path(file_path)
            click.echo(f"  {i}. {file_path}")
            click.echo(f"     相对路径: {rel}")

        # Show format info
        format_info = []
        if format in ['html', 'both']:
            format_info.append(f"HTML: {'Kami 完整（带封面页）' if kami else '简单格式'}")
        if format in ['pdf', 'both']:
            format_info.append(f"PDF: {'Kami 完整（带封面页）' if kami else '简单格式'}")
        if clean:
            format_info.append("已清理 HTML")
        click.echo(f"  格式: {', '.join(format_info)}")

        # Open in browser if requested (only for HTML)
        if (open or print) and format in ['html', 'both']:
            import webbrowser

            # Convert to absolute path
            abs_path = str(output_path.absolute())
            file_url = f"file:///{abs_path.replace(os.sep, '/')}"

            if print:
                file_url += "?print"

            webbrowser.open(file_url)
            click.echo(f"[OK] 已在浏览器中打开")

    except Exception as e:
        click.echo(f"导出失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("item_id")
@click.argument("new_status")
@click.option("--undo", is_flag=True, help="恢复到 inbox")
def status(item_id: str, new_status: str, undo: bool):
    """更改条目状态

    示例：
        kv status <item_id> archived
        kv status <item_id> starred --undo
    """
    if undo:
        new_status = "inbox"

    if new_status not in ["inbox", "archived", "starred", "merged"]:
        click.echo(f"错误: 无效的状态 '{new_status}'", err=True)
        click.echo("有效状态: inbox, archived, starred, merged")
        sys.exit(1)

    item = db.update_item(item_id, status=new_status)

    if not item:
        click.echo(f"错误: 未找到 ID 为 {item_id} 的条目", err=True)
        sys.exit(1)

    click.echo(f"[OK] 状态已更新: {item.title} -> {new_status}")


@cli.command()
@click.argument("item_id")
@click.argument("tag_name")
def tag(item_id: str, tag_name: str):
    """为条目添加标签

    示例：
        kv tag <item_id> Python
        kv tag <item_id> "机器学习"
    """
    tag_obj = db.add_tag_to_item(item_id, tag_name)
    click.echo(f"[OK] 已添加标签: {tag_obj.name}")


@cli.group()
def tags():
    """标签管理

    示例：
        kv tags list
        kv tags rename
        kv tags delete
        kv tags items
    """
    pass


@tags.command("list")
@click.option("--sort", "-s", type=click.Choice(['name', 'count']), default='name', help="排序方式")
def tags_list(sort: str):
    """列出所有标签

    示例：
        kv tags list
        kv tags list -s count
    """
    all_tags = db.get_tags()

    if not all_tags:
        click.echo("暂无标签")
        sys.exit(0)

    if sort == 'count':
        all_tags.sort(key=lambda t: t.use_count, reverse=True)
    else:
        all_tags.sort(key=lambda t: t.name)

    click.echo(f"共 {len(all_tags)} 个标签:\n")

    for tag in all_tags:
        click.echo(f"#{tag.name} ({tag.use_count} 个条目)")


@tags.command("items")
@click.argument("tag_name")
@click.option("--limit", "-l", default=20, help="最大结果数")
def tags_items(tag_name: str, limit: int):
    """列出标签下的所有条目

    示例：
        kv tags items Python
        kv tags items "机器学习" -l 50
    """
    tag_obj = db.find_tag_by_name(tag_name)

    if not tag_obj:
        click.echo(f"未找到标签: {tag_name}")
        sys.exit(1)

    # Get items with this tag
    from kv.core.database import ItemTag, Item

    with db.get_session() as session:
        items = (
            session.query(Item)
            .join(ItemTag)
            .filter(ItemTag.tag_id == tag_obj.id)
            .order_by(Item.created_at.desc())
            .limit(limit)
            .all()
        )

    if not items:
        click.echo(f"标签 '#{tag_name}' 下暂无条目")
        sys.exit(0)

    click.echo(f"标签 '#{tag_name}' 下有 {len(items)} 个条目:\n")

    for i, item in enumerate(items, 1):
        status_emoji = {
            "inbox": "[Inbox]",
            "archived": "[Archived]",
            "starred": "[Starred]",
        }.get(item.status, "[Item]")

        click.echo(f"{i}. {status_emoji} {item.title}")
        click.echo(f"   来源: {item.source_url or '本地'}")
        click.echo(f"   时间: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"   ID: {item.id}")
        click.echo()


@tags.command("rename")
@click.argument("old_name")
@click.argument("new_name")
def tags_rename(old_name: str, new_name: str):
    """重命名标签

    示例：
        kv tags rename Python "Python3"
    """
    tag_obj = db.find_tag_by_name(old_name)

    if not tag_obj:
        click.echo(f"未找到标签: {old_name}")
        sys.exit(1)

    # Check if new name already exists
    existing = db.find_tag_by_name(new_name)
    if existing:
        click.echo(f"错误: 标签 '{new_name}' 已存在", err=True)
        sys.exit(1)

    updated = db.update_tag(tag_obj.id, name=new_name)

    if updated:
        click.echo(f"[OK] 标签已重命名: {old_name} -> {new_name}")
    else:
        click.echo("重命名失败", err=True)
        sys.exit(1)


@tags.command("delete")
@click.argument("tag_name")
@click.confirmation_option(prompt="确认删除标签？")
def tags_delete(tag_name: str):
    """删除标签

    示例：
        kv tags delete Python
    """
    tag_obj = db.find_tag_by_name(tag_name)

    if not tag_obj:
        click.echo(f"未找到标签: {tag_name}")
        sys.exit(1)

    if db.delete_tag(tag_obj.id):
        click.echo(f"[OK] 已删除标签: {tag_name}")
    else:
        click.echo("删除失败", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--description", "-d", help="合集描述")
def collection(name: str, description: Optional[str]):
    """创建新合集

    示例：
        kv collection "Python 学习"
        kv collection "前端开发" -d "前端技术文章"
    """
    try:
        coll = db.create_collection(name, description)
        click.echo(f"[OK] 已创建合集: {coll.name} (ID: {coll.id})")
    except ValueError as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@cli.command()
def collections():
    """列出所有合集"""
    collections = db.get_collections()

    if not collections:
        click.echo("暂无合集")
        sys.exit(0)

    click.echo(f"共 {len(collections)} 个合集:\n")

    for coll in collections:
        click.echo(f"[DIR] {coll.name}")
        if coll.description:
            click.echo(f"   {coll.description}")
        click.echo(f"   ID: {coll.id} | 条目数: {coll.item_count}")
        click.echo()


@cli.command()
@click.argument("item_id")
@click.option("--format", "-f", type=click.Choice(["text", "html"]), default="text", help="输出格式")
def show(item_id: str, format: str):
    """查看条目详细内容

    示例：
        kv show <item_id>
        kv show <item_id> -f html
    """
    item = db.get_item(item_id)

    if not item:
        click.echo(f"错误: 未找到 ID 为 {item_id} 的条目", err=True)
        sys.exit(1)

    # 基本信息
    click.echo(f"标题: {item.title}")
    click.echo(f"ID: {item.id}")
    click.echo(f"状态: {item.status}")

    if item.source_url:
        click.echo(f"来源: {item.source_url}")
    if item.author:
        click.echo(f"作者: {item.author}")
    if item.word_count:
        click.echo(f"字数: {item.word_count}")
    if item.reading_time:
        click.echo(f"阅读时间: {item.reading_time} 分钟")

    click.echo(f"创建时间: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"更新时间: {item.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # 标签
    tags = db.get_item_tags(item_id)
    if tags:
        click.echo(f"标签: {', '.join(tag.name for tag in tags)}")

    # 合集
    if item.collection_id:
        coll = db.get_collection(item.collection_id)
        if coll:
            click.echo(f"合集: {coll.name}")

    # 相似内容
    if item.simhash:
        similar = db.get_similar_items(item_id, threshold=0.75)
        if similar:
            click.echo(f"\n相似内容:")
            for similar_item, similarity in similar[:3]:
                click.echo(f"  - {similar_item.title} (相似度: {similarity:.1%})")

    # 内容
    click.echo("\n" + "="*60)
    if format == "html" and item.content_html:
        click.echo(item.content_html)
    else:
        click.echo(item.content_text or "(无内容)")
    click.echo("="*60)


@cli.command()
@click.argument("source_id")
@click.argument("target_id")
@click.option("--keep-both", is_flag=True, help="保留两个条目，只添加关联")
def merge(source_id: str, target_id: str, keep_both: bool):
    """合并两个条目

    示例：
        kv merge <source_id> <target_id>
        kv merge <source_id> <target_id> --keep-both
    """
    source = db.get_item(source_id)
    target = db.get_item(target_id)

    if not source:
        click.echo(f"错误: 未找到源条目 {source_id}", err=True)
        sys.exit(1)

    if not target:
        click.echo(f"错误: 未找到目标条目 {target_id}", err=True)
        sys.exit(1)

    click.echo(f"源条目: {source.title}")
    click.echo(f"目标条目: {target.title}")

    if not click.confirm("\n确认合并？"):
        click.echo("已取消")
        sys.exit(0)

    try:
        result = dedup.merge_items(source_id, target_id, keep_both=keep_both)

        if keep_both:
            click.echo(f"[OK] 已添加关联: {source.title} -> {target.title}")
        else:
            click.echo(f"[OK] 已合并: {source.title} -> {target.title}")
            click.echo(f"  源条目已标记为 'merged' 状态")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@cli.command()
def stats():
    """显示知识库统计信息"""
    click.echo("知识库统计\n" + "="*40)

    # 统计各类条目数量
    from sqlalchemy import func
    from kv.core.database import Item, Collection, Tag

    with db.get_session() as session:
        # 总条目数
        total_items = session.query(Item).count()

        # 按状态分组统计
        status_counts = {}
        for status in ["inbox", "archived", "starred", "merged"]:
            count = session.query(Item).filter(Item.status == status).count()
            status_counts[status] = count

        # 总字数
        total_words = session.query(
            func.coalesce(func.sum(Item.word_count), 0)
        ).scalar()

        # 总阅读时间
        total_reading_time = session.query(
            func.coalesce(func.sum(Item.reading_time), 0)
        ).scalar()

        # 合集数
        total_collections = session.query(Collection).count()

        # 标签数
        total_tags = session.query(Tag).count()

        # 最新条目
        latest = session.query(Item).order_by(
            Item.created_at.desc()
        ).first()

    # 显示统计
    click.echo(f"📊 总条目数: {total_items}")
    click.echo(f"   📥 收件箱: {status_counts.get('inbox', 0)}")
    click.echo(f"   📦 已归档: {status_counts.get('archived', 0)}")
    click.echo(f"   ⭐ 已加星: {status_counts.get('starred', 0)}")
    click.echo(f"   [Merged] 已合并: {status_counts.get('merged', 0)}")
    click.echo()
    click.echo(f"[DIR] 合集数: {total_collections}")
    click.echo(f"[TAG] 标签数: {total_tags}")
    click.echo()
    click.echo(f"[TEXT] 总字数: {total_words:,}")
    click.echo(f"[TIME] 总阅读时间: {total_reading_time} 分钟 ({total_reading_time/60:.1f} 小时)")

    if latest:
        click.echo()
        click.echo(f"[NEW] 最新添加: {latest.title}")
        click.echo(f"   时间: {latest.created_at.strftime('%Y-%m-%d %H:%M')}")


@cli.command()
@click.argument("item_id")
@click.confirmation_option(prompt="确认删除？")
def delete(item_id: str):
    """删除条目

    示例：
        kv delete <item_id>
    """
    item = db.get_item(item_id)

    if not item:
        click.echo(f"错误: 未找到 ID 为 {item_id} 的条目", err=True)
        sys.exit(1)

    click.echo(f"正在删除: {item.title}")

    if db.delete_item(item_id):
        click.echo(f"[OK] 已删除: {item.title}")
    else:
        click.echo(f"删除失败", err=True)
        sys.exit(1)


@cli.command()
@click.argument("item_id")
@click.option("--threshold", "-t", default=0.75, type=float, help="相似度阈值 (0-1)")
@click.option("--limit", "-l", default=10, help="最大结果数")
def similar(item_id: str, threshold: float, limit: int):
    """查找相似内容

    示例：
        kv similar <item_id>
        kv similar <item_id> -t 0.8 -l 5
    """
    item = db.get_item(item_id)

    if not item:
        click.echo(f"错误: 未找到 ID 为 {item_id} 的条目", err=True)
        sys.exit(1)

    if not item.simhash:
        click.echo("该条目没有 simhash，无法查找相似内容")
        sys.exit(0)

    click.echo(f"正在查找与「{item.title}」相似的内容...\n")

    similar_items = db.get_similar_items(item_id, threshold=threshold)

    if not similar_items:
        click.echo(f"未找到相似度 > {threshold:.0%} 的内容")
        sys.exit(0)

    click.echo(f"找到 {len(similar_items)} 个相似内容:\n")

    for similar_item, similarity in similar_items[:limit]:
        similarity_percent = similarity * 100

        # 根据相似度显示不同的图标
        if similarity >= 0.9:
            icon = "🔴"
            level = "高度相似"
        elif similarity >= 0.8:
            icon = "🟠"
            level = "相似"
        else:
            icon = "🟡"
            level = "可能相似"

        click.echo(f"{icon} {similar_item.title}")
        click.echo(f"   相似度: {similarity:.1%} ({level})")
        click.echo(f"   来源: {similar_item.source_url or '本地'}")
        click.echo(f"   ID: {similar_item.id}")
        click.echo()


@cli.command("import")
@click.argument("file_path")
@click.option("--title", "-t", help="自定义标题")
@click.option("--author", "-a", help="作者")
@click.option("--collection", "-c", help="合集名称")
@click.option("--no-dedup", is_flag=True, help="跳过重复检测")
def import_cmd(file_path: str, title: Optional[str], author: Optional[str],
               collection: Optional[str], no_dedup: bool):
    """导入本地文件到知识库

    示例：
        kv import article.html
        kv import notes.md -t "我的笔记"
        kv import document.txt -c "文档合集"
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        click.echo(f"错误: 文件不存在: {file_path}", err=True)
        sys.exit(1)

    # Determine file type
    suffix = file_path_obj.suffix.lower()

    try:
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            content_text = f.read()

        # Parse based on file type
        if suffix in ['.html', '.htm']:
            # HTML file
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content_text, 'lxml')

            # Extract title
            if not title:
                title_tag = soup.find('title')
                title = title_tag.get_text() if title_tag else file_path_obj.stem

            # Extract content
            content = str(soup.body) if soup.body else content_text

        elif suffix in ['.md', '.markdown']:
            # Markdown file
            if not title:
                # Try to extract title from first heading
                for line in content_text.split('\n'):
                    if line.startswith('#'):
                        title = line.lstrip('#').strip()
                        break
                if not title:
                    title = file_path_obj.stem

            # Simple markdown to HTML conversion
            import re
            content_html = content_text

            # Convert markdown headers
            content_html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content_html, flags=re.MULTILINE)
            content_html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content_html, flags=re.MULTILINE)
            content_html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content_html, flags=re.MULTILINE)

            # Convert paragraphs
            paragraphs = content_html.split('\n\n')
            content = '\n'.join(f'<p>{p}</p>' for p in paragraphs if p.strip())

        elif suffix in ['.txt']:
            # Plain text file
            if not title:
                title = file_path_obj.stem

            # Convert to HTML paragraphs
            paragraphs = content_text.split('\n\n')
            content = '\n'.join(f'<p>{p}</p>' for p in paragraphs if p.strip())

        else:
            click.echo(f"错误: 不支持的文件类型: {suffix}", err=True)
            click.echo("支持的格式: .html, .htm, .md, .markdown, .txt")
            sys.exit(1)

        # Compute simhash
        simhash = generate_simhash(content_text)

        # Check for duplicates
        if not no_dedup:
            duplicates = dedup.find_duplicates(content_text)

            if duplicates:
                click.echo(f"\n发现 {len(duplicates)} 个相似内容:")
                for item, similarity in duplicates[:5]:
                    click.echo(
                        f"  - {item.title} (相似度: {similarity:.1%}) "
                        f"[{item.source_type}]"
                    )

                best_match = duplicates[0]
                if best_match[1] > 0.9:
                    if click.confirm("\n内容高度相似，是否跳过导入？"):
                        click.echo("已跳过导入")
                        sys.exit(0)

        # Find or create collection
        collection_id = None
        if collection:
            coll = db.get_collection_by_name(collection)
            if not coll:
                coll = db.create_collection(collection)
                click.echo(f"创建合集: {collection}")
            collection_id = coll.id

        # Calculate word count and reading time
        word_count = len(content_text.split())
        reading_time = max(1, round(word_count / 200))

        # Create item
        item = db.create_item(
            title=title,
            source_type="local",
            source_url=str(file_path_obj.absolute()),
            author=author,
            content_html=content,
            content_text=content_text,
            content_markdown=content_text if suffix in ['.md', '.markdown'] else None,
            word_count=word_count,
            reading_time=reading_time,
            collection_id=collection_id,
            simhash=simhash,
        )

        click.echo(f"\n[OK] 成功导入: {item.title}")
        click.echo(f"  ID: {item.id}")
        click.echo(f"  字数: {word_count}")
        click.echo(f"  阅读时间: {reading_time} 分钟")

    except Exception as e:
        click.echo(f"导入失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.group()
def config():
    """配置管理

    示例：
        kv config get dedup.threshold
        kv config set dedup.threshold 0.8
        kv config init
    """
    pass


@config.command("init")
def config_init():
    """初始化配置文件"""
    click.echo(f"配置文件路径: {config_service.get_config_file_path()}")

    if config_service.config_file.exists():
        if not click.confirm("配置文件已存在，是否覆盖？"):
            click.echo("已取消")
            sys.exit(0)

    if config_service.init_default_config():
        click.echo("[OK] 已创建默认配置文件")
        click.echo(f"\n配置文件位置: {config_service.get_config_file_path()}")
        click.echo("\n默认配置:")
        click.echo("  dedup.threshold: 0.75  # 相似度阈值")
        click.echo("  scraper.timeout: 30     # 抓取超时时间（秒）")
        click.echo("  export.default_format: html  # 默认导出格式")
        click.echo("  search.limit: 20         # 搜索结果数量")
    else:
        click.echo("创建配置文件失败", err=True)
        sys.exit(1)


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """获取配置值

    示例：
        kv config get dedup.threshold
    """
    value = config_service.get(key)

    if value is None:
        click.echo(f"未找到配置项: {key}")
        sys.exit(1)

    if hasattr(value, 'items'):
        click.echo(f"{key}:")
        for k, v in value.items():
            click.echo(f"  {k}: {v}")
    elif type(value) == list:
        click.echo(f"{key}: {', '.join(str(v) for v in value)}")
    else:
        click.echo(f"{key}: {value}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置配置值

    示例：
        kv config set dedup.threshold 0.8
        kv config set scraper.timeout 60
    """
    # Try to parse value as number or boolean
    try:
        if value.lower() in ('true', 'yes', 'on'):
            parsed_value = True
        elif value.lower() in ('false', 'no', 'off'):
            parsed_value = False
        else:
            parsed_value = float(value) if '.' in value else int(value)
    except ValueError:
        parsed_value = value

    if config_service.set(key, parsed_value):
        click.echo(f"[OK] 已设置: {key} = {parsed_value}")
    else:
        click.echo("设置失败", err=True)
        sys.exit(1)


@config.command("list")
def config_list():
    """列出所有配置"""
    config_dict = config_service.load_config()

    if not config_dict:
        click.echo("配置文件不存在或为空")
        click.echo(f"路径: {config_service.get_config_file_path()}")
        click.echo("\n使用 'kv config init' 创建默认配置")
        sys.exit(0)

    click.echo(f"配置文件: {config_service.get_config_file_path()}\n")
    _print_config_dict(config_dict, indent=0)


def _print_config_dict(d: dict, indent: int = 0):
    """Helper function to print config dictionary"""
    prefix = "  " * indent
    for key, value in d.items():
        # Check if value is dict-like
        if hasattr(value, 'items'):
            click.echo(f"{prefix}{key}:")
            # Convert to regular dict to avoid issues with YAML types
            _print_config_dict(dict(value.items()), indent + 1)
        elif type(value) == list:
            click.echo(f"{prefix}{key}: {', '.join(str(v) for v in value)}")
        else:
            click.echo(f"{prefix}{key}: {value}")


@config.command("edit")
def config_edit():
    """编辑配置文件"""
    import subprocess

    config_file = config_service.get_config_file_path()

    # Create default config if it doesn't exist
    if not config_service.config_file.exists():
        click.echo("配置文件不存在，正在创建...")
        config_service.init_default_config()

    # Open in default editor
    click.echo(f"正在打开配置文件: {config_file}")

    if os.name == 'nt':  # Windows
        os.startfile(config_file)
    elif os.name == 'posix':  # macOS/Linux
        editor = os.environ.get('EDITOR', 'vi')
        subprocess.call([editor, config_file])
    else:
        click.echo("不支持的操作系统", err=True)
        sys.exit(1)


@cli.group("exports")
def export_cmd():
    """导出文件管理

    示例：
        kv exports list
        kv exports clean
        kv exports stats
        kv exports open
    """
    pass


@export_cmd.command("list")
@click.option("--format", "-f", help="筛选文件格式")
@click.option("--limit", "-l", default=20, help="最大结果数")
def export_list(format: Optional[str], limit: int):
    """列出所有导出的文件

    示例：
        kv export list
        kv export list -f html
        kv export list -l 50
    """
    pattern = f"*.{format}" if format else "*"
    exports = export_manager.list_exports(pattern=pattern, recursive=True)

    if not exports:
        click.echo("没有找到导出文件")
        sys.exit(0)

    click.echo(f"导出目录: {export_manager.get_export_root()}")
    click.echo(f"共 {len(exports)} 个文件\n")

    # Show exports limited by limit
    for i, export in enumerate(exports[:limit]):
        # Format size
        size_kb = export["size"] / 1024
        if size_kb < 1024:
            size_str = f"{size_kb:.1f} KB"
        else:
            size_mb = size_kb / 1024
            size_str = f"{size_mb:.1f} MB"

        click.echo(f"{i+1}. {export['relative_path']}")
        click.echo(f"   大小: {size_str}")
        click.echo(f"   时间: {export['modified'].strftime('%Y-%m-%d %H:%M')}")

    if len(exports) > limit:
        click.echo(f"\n... 还有 {len(exports) - limit} 个文件")


@export_cmd.command("stats")
def export_stats_cmd():
    """显示导出文件统计信息"""
    stats = export_manager.get_export_stats()

    click.echo("导出文件统计\n" + "="*40)
    click.echo(f"导出目录: {stats['export_root']}")
    click.echo(f"总文件数: {stats['total_count']}")
    click.echo(f"总大小: {stats['total_size_mb']:.2f} MB")
    click.echo()

    if stats['by_format']:
        click.echo("按格式:")
        for fmt, count in sorted(stats['by_format'].items()):
            click.echo(f"  .{fmt}: {count}")
        click.echo()

    if stats['by_date']:
        click.echo("按月份:")
        for date, count in sorted(stats['by_date'].items(), reverse=True)[:6]:
            click.echo(f"  {date}: {count}")


@export_cmd.command("clean")
@click.option("--days", "-d", default=30, help="保留最近 N 天的文件")
@click.option("--keep", "-k", type=int, help="每个目录最多保留 N 个文件")
@click.option("--all", is_flag=True, help="删除所有导出文件")
@click.option("--dry-run", is_flag=True, help="只显示将要删除的文件，不实际删除")
def export_clean(days: int, keep: Optional[int], all: bool, dry_run: bool):
    """清理旧的导出文件

    示例：
        kv export clean              # 清理30天前的文件
        kv export clean -d 7         # 清理7天前的文件
        kv export clean -k 10        # 每个目录最多保留10个文件
        kv export clean --all        # 删除所有导出文件
        kv export clean --dry-run    # 预览将要删除的文件
    """
    if all:
        files = export_manager.clean_all(dry_run=dry_run)
        action = "将要删除" if dry_run else "已删除"
        click.echo(f"{action}所有文件 ({len(files)} 个)")
    else:
        files = export_manager.clean_old_exports(
            keep_days=days,
            keep_count=keep,
            dry_run=dry_run
        )
        action = "将要删除" if dry_run else "已删除"
        click.echo(f"{action} {len(files)} 个文件 (保留 {days} 天内的文件", end="")
        if keep:
            click.echo(f", 每个目录最多 {keep} 个文件)")
        else:
            click.echo(")")

    if not dry_run and files:
        click.echo(f"[OK] 清理完成")

    if files:
        click.echo("\n文件列表:")
        for file_path in files[:20]:
            rel_path = export_manager.get_relative_path(file_path)
            click.echo(f"  - {rel_path}")

        if len(files) > 20:
            click.echo(f"  ... 还有 {len(files) - 20} 个文件")
    elif not all:
        click.echo("没有需要清理的文件")


@export_cmd.command("open")
def export_open():
    """在文件管理器中打开导出目录"""
    import subprocess
    import platform

    export_root = export_manager.get_export_root()

    click.echo(f"正在打开: {export_root}")

    if platform.system() == 'Windows':
        os.startfile(str(export_root))
    elif platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', str(export_root)])
    else:  # Linux
        subprocess.call(['xdg-open', str(export_root)])


@export_cmd.command("batch")
@click.option("--status", "-s", help="按状态筛选")
@click.option("--collection", "-c", help="按合集筛选")
@click.option("--tag", "-t", help="按标签筛选")
@click.option("--limit", "-l", default=100, help="最大导出数量")
@click.option("--open", is_flag=True, help="完成后打开导出目录")
def export_batch(status: Optional[str], collection: Optional[str], tag: Optional[str],
                limit: int, open: bool):
    """批量导出条目

    示例：
        kv exports batch                          # 导出所有收件箱条目
        kv exports batch -s archived              # 导出已归档条目
        kv exports batch -c "Python学习"           # 导出指定合集
        kv exports batch -t "教程" -l 50           # 导出指定标签，最多50个
    """
    from kv.core.database import Item, ItemTag

    with db.get_session() as session:
        query = session.query(Item).filter(Item.status != 'merged')

        # Apply filters
        if status:
            query = query.filter(Item.status == status)
        else:
            # Default to inbox if not specified
            query = query.filter(Item.status == 'inbox')

        if collection:
            coll = db.get_collection_by_name(collection)
            if coll:
                query = query.filter(Item.collection_id == coll.id)
            else:
                click.echo(f"错误: 未找到合集 '{collection}'", err=True)
                sys.exit(1)

        if tag:
            tag_obj = db.find_tag_by_name(tag)
            if tag_obj:
                query = query.join(ItemTag).filter(ItemTag.tag_id == tag_obj.id)
            else:
                click.echo(f"未找到标签 '{tag}'")
                sys.exit(0)

        items = query.order_by(Item.created_at.desc()).limit(limit).all()

    if not items:
        click.echo("没有找到符合条件的条目")
        sys.exit(0)

    click.echo(f"准备导出 {len(items)} 个条目...\n")

    success_count = 0
    failed_items = []

    for i, item in enumerate(items, 1):
        try:
            click.echo(f"[{i}/{len(items)}] 正在导出: {item.title[:50]}...")

            # Generate export
            content = item.content_html or f"<p>{item.content_text}</p>"

            # Get export path
            organize_method = config_service.get('export.organize_by', 'date')
            export_format = config_service.get('export.default_format', 'html')

            collection_name = None
            if organize_method == 'collection' and item.collection_id:
                coll = db.get_collection(item.collection_id)
                collection_name = coll.name if coll else None

            output_path = export_manager.get_export_path(
                item_title=item.title,
                item_date=item.created_at,
                collection_name=collection_name,
                export_format=export_format,
                organize_by=organize_method if organize_method != 'none' else None
            )

            # Generate HTML
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
                temp_path = Path(tmp.name)

            html_exporter.generate_html(
                title=item.title,
                content=content,
                author=item.author,
                url=item.source_url,
                created_at=item.created_at,
                output_path=str(temp_path)
            )

            # Move to final location
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_path), str(output_path))

            success_count += 1

        except Exception as e:
            click.echo(f"  ✗ 失败: {e}")
            failed_items.append((item.title, str(e)))

    click.echo(f"\n[OK] 批量导出完成!")
    click.echo(f"  成功: {success_count}/{len(items)}")

    if failed_items:
        click.echo(f"\n失败列表:")
        for title, error in failed_items[:10]:
            click.echo(f"  ✗ {title[:50]}")
            click.echo(f"    {error}")
        if len(failed_items) > 10:
            click.echo(f"  ... 还有 {len(failed_items) - 10} 个失败")

    if open:
        import subprocess
        import platform
        export_root = export_manager.get_export_root()

        if platform.system() == 'Windows':
            os.startfile(str(export_root))
        elif platform.system() == 'Darwin':
            subprocess.call(['open', str(export_root)])
        else:
            subprocess.call(['xdg-open', str(export_root)])


@cli.group()
def backup():
    """数据库备份与恢复

    示例：
        kv backup create
        kv backup list
        kv backup restore
        kv backup clean
    """
    pass


@backup.command("create")
@click.option("--name", "-n", help="备份名称")
@click.option("--description", "-d", help="备份描述")
def backup_create(name: Optional[str], description: Optional[str]):
    """创建数据库备份

    示例：
        kv backup create
        kv backup create -n "升级前备份" -d "升级到新版本前"
    """
    try:
        backup_path = backup_service.create_backup(name=name, description=description)

        # Get file size
        size_mb = backup_path.stat().st_size / (1024 * 1024)

        click.echo(f"[OK] 备份创建成功")
        click.echo(f"  文件: {backup_path.name}")
        click.echo(f"  大小: {size_mb:.2f} MB")
        click.echo(f"  位置: {backup_path.parent}")

    except Exception as e:
        click.echo(f"备份失败: {e}", err=True)
        sys.exit(1)


@backup.command("list")
def backup_list():
    """列出所有备份

    示例：
        kv backup list
    """
    backups = backup_service.list_backups()

    if not backups:
        click.echo("暂无备份")
        click.echo(f"备份目录: {backup_service.backup_dir}")
        sys.exit(0)

    click.echo(f"共 {len(backups)} 个备份\n")
    click.echo(f"备份目录: {backup_service.backup_dir}\n")

    for i, info in enumerate(backups, 1):
        size_mb = info["size"] / (1024 * 1024)
        created_str = info["created"].strftime("%Y-%m-%d %H:%M:%S")

        click.echo(f"{i}. {info['name']}")
        click.echo(f"   大小: {size_mb:.2f} MB")
        click.echo(f"   时间: {created_str}")

        if "description" in info:
            click.echo(f"   描述: {info['description']}")

        click.echo()


@backup.command("restore")
@click.argument("backup_name")
@click.confirmation_option(prompt="确认要恢复此备份？当前数据库将被覆盖。")
def backup_restore(backup_name: str):
    """从备份恢复数据库

    示例：
        kv backup restore 20260512_163000.db
    """
    try:
        backup_path = backup_service.backup_dir / backup_name

        if not backup_path.exists():
            click.echo(f"错误: 备份文件不存在: {backup_name}", err=True)
            click.echo(f"\n可用备份:")
            backups = backup_service.list_backups()
            for info in backups[:5]:
                click.echo(f"  - {info['name']}")
            sys.exit(1)

        backup_service.restore_backup(str(backup_path))

        click.echo(f"[OK] 数据库已从备份恢复")
        click.echo(f"  备份: {backup_name}")

    except Exception as e:
        click.echo(f"恢复失败: {e}", err=True)
        sys.exit(1)


@backup.command("delete")
@click.argument("backup_name")
@click.confirmation_option(prompt="确认删除此备份？")
def backup_delete(backup_name: str):
    """删除备份

    示例：
        kv backup delete 20260512_163000.db
    """
    if backup_service.delete_backup(backup_name):
        click.echo(f"[OK] 已删除备份: {backup_name}")
    else:
        click.echo(f"错误: 备份文件不存在: {backup_name}", err=True)
        sys.exit(1)


@backup.command("clean")
@click.option("--keep", "-k", default=10, help="保留最近 N 个备份")
@click.option("--dry-run", is_flag=True, help="只显示将要删除的备份，不实际删除")
def backup_clean(keep: int, dry_run: bool):
    """清理旧备份

    示例：
        kv backup clean              # 保留最近10个备份
        kv backup clean -k 5         # 保留最近5个备份
        kv backup clean --dry-run   # 预览将要删除的备份
    """
    deleted = backup_service.clean_old_backups(keep_count=keep, dry_run=dry_run)

    if not deleted:
        click.echo("没有需要清理的备份")
        sys.exit(0)

    action = "将要删除" if dry_run else "已删除"
    click.echo(f"{action} {len(deleted)} 个旧备份 (保留最近 {keep} 个)\n")

    for backup_path in deleted:
        click.echo(f"  - {backup_path.name}")

    if not dry_run and deleted:
        click.echo(f"\n[OK] 清理完成")


if __name__ == "__main__":
    cli()
