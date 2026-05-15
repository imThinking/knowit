"""Export commands - Export items to HTML/PDF"""

import sys
import os
import click
from pathlib import Path

from kv.services.database import db
from kv.services.pdf_export import html_exporter
from kv.services.export_manager import export_manager
from kv.core.exceptions import (
    ItemNotFoundError,
    WeasyPrintNotFoundError,
    PDFGenerationError,
)


@click.command()
@click.argument("item_id")
@click.option("--output", "-o", help="输出文件路径")
@click.option("--format", "-f", default="html", type=click.Choice(["html", "pdf"]), help="输出格式")
@click.option("--open", is_flag=True, help="自动打开文件")
@click.option("--print", is_flag=True, help="打印到标准输出")
@click.option("--organize-by", default="date", type=click.Choice(["date", "collection", "flat"]), help="导出组织方式")
@click.option("--simple", is_flag=True, help="使用简化格式（无封面）")
@click.option("--kami", is_flag=True, help="使用 Kami 设计系统（默认）")
@click.option("--clean", is_flag=True, help="清理 HTML 内容")
@click.option("--font-dir", help="字体目录路径")
def export(item_id: str, output: str, format: str, open: bool, print: bool, organize_by: str, simple: bool, kami: bool, clean: bool, font_dir: str):
    """导出条目为 HTML 或 PDF

    示例：
        kv export <item_id>
        kv export <item_id> -f pdf -o output.pdf
        kv export <item_id> --organize-by collection
    """
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目: {item_id}", err=True)
        return

    try:
        # Get export path
        collection_name = None
        if organize_by == "collection" and item.collection_id:
            coll = db.get_collection(item.collection_id)
            collection_name = coll.name if coll else None

        if not output:
            export_path = export_manager.get_export_path(
                item_title=item.title,
                item_date=item.created_at,
                collection_name=collection_name,
                export_format=format,
                organize_by=organize_by
            )
        else:
            export_path = Path(output)

        # Generate content
        if format == "pdf":
            html_exporter.generate_pdf(
                title=item.title,
                content=item.content_html or "",
                author=item.author,
                url=item.source_url,
                created_at=item.created_at,
                output_path=str(export_path),
                clean=clean,
                font_dir=font_dir,
            )
        else:
            if simple:
                html_exporter.generate_html_simple(
                    title=item.title,
                    content=item.content_html or "",
                    author=item.author,
                    url=item.source_url,
                    created_at=item.created_at,
                    output_path=str(export_path),
                    clean=clean,
                )
            else:
                html_exporter.generate_html(
                    title=item.title,
                    content=item.content_html or "",
                    author=item.author,
                    url=item.source_url,
                    created_at=item.created_at,
                    output_path=str(export_path),
                    clean=clean,
                )

        # Get relative path for display
        relative_path = export_manager.get_relative_path(export_path)

        if print:
            with open(export_path, 'r', encoding='utf-8') as f:
                click.echo(f.read())
        else:
            click.echo(f"✓ 已导出到: {relative_path}")

        # Open file if requested
        if open:
            os.startfile(str(export_path)) if sys.platform == "win32" else os.system(f"open '{export_path}'")

    except WeasyPrintNotFoundError as e:
        click.echo(f"错误: {e.message}", err=True)
        sys.exit(1)
    except PDFGenerationError as e:
        click.echo(f"PDF 生成失败: {e.message}", err=True)
        sys.exit(1)
