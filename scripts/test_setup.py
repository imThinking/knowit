"""
KnowIt 快速测试脚本

在 PowerShell 中运行：
    python scripts/test_setup.py
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """测试核心模块导入"""
    print("测试模块导入...")

    try:
        from kv.core.config import Config
        print("  ✓ kv.core.config")
    except ImportError as e:
        print(f"  ✗ kv.core.config: {e}")
        return False

    try:
        from kv.core.database import Base, Item, Collection
        print("  ✓ kv.core.database")
    except ImportError as e:
        print(f"  ✗ kv.core.database: {e}")
        return False

    try:
        import click
        print("  ✓ click")
    except ImportError:
        print("  ✗ click: 请运行 'pip install click'")
        return False

    try:
        import sqlalchemy
        print("  ✓ sqlalchemy")
    except ImportError:
        print("  ✗ sqlalchemy: 请运行 'pip install sqlalchemy'")
        return False

    print("\n所有核心模块导入成功！")
    return True


def test_database():
    """测试数据库连接"""
    print("\n测试数据库...")

    from kv.core.config import Config
    from kv.core.database import Base
    from sqlalchemy import create_engine

    config = Config()
    engine = create_engine(f"sqlite:///{config.db_path}")

    try:
        # 尝试连接数据库
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"  ✓ 数据库连接成功")
        print(f"  ✓ 已创建表: {', '.join(tables)}")
        return True
    except Exception as e:
        print(f"  ✗ 数据库连接失败: {e}")
        return False


def test_cli():
    """测试 CLI 模块"""
    print("\n测试 CLI...")

    try:
        from kv.cli import cli
        print("  ✓ kv.cli 模块加载成功")

        # 测试 click 命令
        if hasattr(cli, 'commands'):
            print(f"  ✓ 可用命令: {list(cli.commands.keys())}")

        return True
    except ImportError as e:
        print(f"  ✗ CLI 模块加载失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("KnowIt 环境测试")
    print("=" * 50)

    results = []
    results.append(test_imports())
    results.append(test_database())
    results.append(test_cli())

    print("\n" + "=" * 50)
    if all(results):
        print("✓ 所有测试通过！环境已就绪。")
        print("\n下一步：")
        print("  python -m kv.cli --help")
    else:
        print("✗ 部分测试失败，请检查上述错误")
        print("\n建议：")
        print("  1. 确保已安装依赖: pip install click sqlalchemy")
        print("  2. 初始化数据库: python scripts/init_db.py")

    print("=" * 50)


if __name__ == "__main__":
    main()
