"""System commands - Stats, backup, export management"""

import sys
import click

from kv.services.database import db
from kv.services.backup_service import backup_service
from kv.services.export_manager import export_manager


@click.command()
def stats():
    """显示知识库统计信息"""
    # Get all items
    all_items = db.get_items(limit=None, status=None)

    # Count by status
    status_counts = {}
    for item in all_items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1

    # Count by source type
    source_counts = {}
    for item in all_items:
        source_counts[item.source_type] = source_counts.get(item.source_type, 0) + 1

    # Total words and reading time
    total_words = sum(item.word_count or 0 for item in all_items)
    total_reading_time = sum(item.reading_time or 0 for item in all_items)

    # Collections and tags
    collections = db.get_collections()
    tags = db.get_tags()

    click.echo("\n📊 知识库统计\n")
    click.echo(f"总条目数: {len(all_items)}")

    if status_counts:
        click.echo("\n按状态:")
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            status_icon = {"inbox": "📥", "archived": "📦", "starred": "⭐", "merged": "🔗"}.get(status, "📄")
            click.echo(f"  {status_icon} {status}: {count}")

    if source_counts:
        click.echo("\n按来源:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  {source}: {count}")

    click.echo(f"\n总字数: {total_words:,}")
    click.echo(f"总阅读时间: {total_reading_time} 分钟 ({total_reading_time / 60:.1f} 小时)")
    click.echo(f"\n合集数: {len(collections)}")
    click.echo(f"标签数: {len(tags)}")

    # Export stats
    export_stats = export_manager.get_export_stats()
    click.echo(f"\n导出文件:")
    click.echo(f"  总数: {export_stats['total_count']}")
    click.echo(f"  总大小: {export_stats['total_size_mb']:.2f} MB")


@click.group()
def backup():
    """备份管理"""
    pass


@backup.command("create")
@click.option("--name", "-n", help="备份名称")
@click.option("--description", "-d", help="备份描述")
def backup_create(name: str, description: str):
    """创建数据库备份

    示例：
        kv backup create
        kv backup create -n "backup_before_changes"
    """
    try:
        backup_path = backup_service.create_backup(name=name, description=description)
        click.echo(f"✓ 已创建备份: {backup_path}")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@backup.command("list")
def backup_list():
    """列出所有备份"""
    backups = backup_service.list_backups()

    if not backups:
        click.echo("没有可用的备份")
        return

    click.echo(f"\n共有 {len(backups)} 个备份:\n")

    for i, backup_info in enumerate(backups, 1):
        click.echo(f"{i}. {backup_info['name']}")
        if backup_info.get('description'):
            click.echo(f"   描述: {backup_info['description']}")
        click.echo(f"   创建时间: {backup_info['created']}")
        click.echo(f"   大小: {backup_info['size_mb']:.2f} MB")
        click.echo(f"   路径: {backup_info['path']}")
        click.echo()


@backup.command("restore")
@click.argument("backup_name")
@click.option("--force", is_flag=True, help="强制覆盖当前数据库")
def backup_restore(backup_name: str, force: bool):
    """从备份恢复数据库

    示例：
        kv backup restore backup_20250115_120000
        kv backup restore backup_name --force
    """
    if not force:
        click.echo("警告: 这将覆盖当前数据库。使用 --force 确认。")
        return

    try:
        backup_service.restore_backup(backup_name)
        click.echo(f"✓ 已从备份 '{backup_name}' 恢复")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@backup.command("delete")
@click.argument("backup_name")
def backup_delete(backup_name: str):
    """删除备份

    示例：
        kv backup delete backup_name
    """
    if not click.confirm(f"确认删除备份 '{backup_name}'?"):
        return

    try:
        backup_service.delete_backup(backup_name)
        click.echo(f"✓ 已删除备份 '{backup_name}'")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)


@backup.command("clean")
@click.option("--keep", "-k", default=10, help="保留备份数量")
@click.option("--dry-run", is_flag=True, help="只显示将要删除的备份")
def backup_clean(keep: int, dry_run: bool):
    """清理旧备份

    示例：
        kv backup clean --keep 5
        kv backup clean --keep 5 --dry-run
    """
    try:
        deleted = backup_service.clean_old_backups(keep=keep, dry_run=dry_run)

        if not deleted:
            click.echo("没有需要清理的备份")
            return

        if dry_run:
            click.echo(f"将删除 {len(deleted)} 个备份:")
        else:
            click.echo(f"已删除 {len(deleted)} 个备份:")

        for backup_path in deleted:
            click.echo(f"  - {backup_path}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)


@click.group()
def export_cmd():
    """导出文件管理"""
    pass


@export_cmd.command("list")
@click.option("--format", "-f", type=click.Choice(["html", "pdf"]), help="按格式筛选")
@click.option("--limit", "-l", default=50, help="最大结果数")
def export_list(format: str, limit: int):
    """列出导出的文件

    示例：
        kv exports list
        kv exports list --format pdf --limit 20
    """
    pattern = f"*.{format}" if format else "*"
    exports = export_manager.list_exports(pattern=pattern)

    exports = exports[:limit]

    if not exports:
        click.echo("没有导出文件")
        return

    click.echo(f"\n共有 {len(exports)} 个导出文件:\n")

    for export_info in exports:
        click.echo(f"📄 {export_info['relative_path']}")
        click.echo(f"   大小: {export_info['size'] / 1024:.1f} KB")
        click.echo(f"   创建时间: {export_info['created'].strftime('%Y-%m-%d %H:%M')}")
        click.echo()


@export_cmd.command("stats")
def export_stats_cmd():
    """显示导出统计信息"""
    stats = export_manager.get_export_stats()

    click.echo("\n导出文件统计:\n")
    click.echo(f"总数: {stats['total_count']}")
    click.echo(f"总大小: {stats['total_size_mb']:.2f} MB")

    if stats['by_format']:
        click.echo("\n按格式:")
        for fmt, count in sorted(stats['by_format'].items()):
            click.echo(f"  {fmt}: {count}")

    if stats['by_date']:
        click.echo("\n按月份:")
        for date, count in sorted(stats['by_date'].items(), reverse=True):
            click.echo(f"  {date}: {count}")

    click.echo(f"\n导出目录: {stats['export_root']}")


@export_cmd.command("clean")
@click.option("--days", "-d", default=30, help="保留天数")
@click.option("--keep", "-k", type=int, help="每目录保留文件数")
@click.option("--all", is_flag=True, help="删除所有导出文件")
@click.option("--dry-run", is_flag=True, help="只显示将要删除的文件")
def export_clean(days: int, keep: int, all: bool, dry_run: bool):
    """清理导出文件

    示例：
        kv exports clean --days 30
        kv exports clean --keep 10 --dry-run
        kv exports clean --all
    """
    if all:
        deleted = export_manager.clean_all(dry_run=dry_run)
    else:
        deleted = export_manager.clean_old_exports(keep_days=days, keep_count=keep, dry_run=dry_run)

    if not deleted:
        click.echo("没有需要清理的文件")
        return

    if dry_run:
        click.echo(f"将删除 {len(deleted)} 个文件:")
    else:
        click.echo(f"已删除 {len(deleted)} 个文件:")

    for file_path in deleted:
        click.echo(f"  - {file_path.relative_to(export_manager.get_export_root())}")


@export_cmd.command("batch")
@click.option("--status", "-s", type=click.Choice(["inbox", "archived", "starred"]), help="按状态筛选")
@click.option("--collection", "-c", help="按合集筛选")
@click.option("--tag", "-t", help="按标签筛选")
@click.option("--format", "-f", default="html", type=click.Choice(["html", "pdf"]), help="输出格式")
@click.option("--organize-by", default="date", type=click.Choice(["date", "collection", "flat"]), help="组织方式")
@click.option("--clean", is_flag=True, help="清理 HTML 内容")
def export_batch(status: str, collection: str, tag: str, format: str, organize_by: str, clean: bool):
    """批量导出条目

    示例：
        kv exports batch -s archived -f pdf
        kv exports batch -c "Python" --organize-by collection
    """
    # Get items based on filters
    collection_id = None
    if collection:
        coll = db.get_collection_by_name(collection)
        if not coll:
            click.echo(f"错误: 未找到合集: {collection}", err=True)
            return
        collection_id = coll.id

    items = db.get_items(status=status, collection_id=collection_id, limit=1000)

    # Filter by tag if specified
    if tag:
        filtered_items = []
        for item in items:
            item_tags = db.get_item_tags(item.id)
            tag_names = [t.name for t in item_tags]
            if tag in tag_names:
                filtered_items.append(item)
        items = filtered_items

    if not items:
        click.echo("没有符合条件的条目")
        return

    click.echo(f"将导出 {len(items)} 个条目...\n")

    success_count = 0
    for i, item in enumerate(items, 1):
        try:
            from kv.services.pdf_export import html_exporter

            # Get export path
            collection_name = None
            if organize_by == "collection" and item.collection_id:
                coll = db.get_collection(item.collection_id)
                collection_name = coll.name if coll else None

            export_path = export_manager.get_export_path(
                item_title=item.title,
                item_date=item.created_at,
                collection_name=collection_name,
                export_format=format,
                organize_by=organize_by
            )

            # Generate export
            if format == "pdf":
                html_exporter.generate_pdf(
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

            relative_path = export_manager.get_relative_path(export_path)
            click.echo(f"[{i}/{len(items)}] ✓ {relative_path}")
            success_count += 1

        except Exception as e:
            click.echo(f"[{i}/{len(items)}] ✗ {item.title}: {e}")

    click.echo(f"\n完成! 成功导出 {success_count}/{len(items)} 个条目")
