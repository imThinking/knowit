"""KnowIt CLI 命令行接口"""

import click


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """KnowIt - 你的第二大脑，优雅地归集网络碎片。"""
    pass


@cli.command()
@click.argument("url")
def add(url):
    """添加网页到知识库

    示例：
        kv add https://example.com/article
    """
    click.echo(f"正在添加: {url}")
    click.echo("✓ 功能开发中...")


@cli.command()
@click.argument("query")
def search(query):
    """搜索知识库

    示例：
        kv search "Python 异步"
    """
    click.echo(f"正在搜索: {query}")
    click.echo("✓ 功能开发中...")


if __name__ == "__main__":
    cli()
