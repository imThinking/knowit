"""
数据库初始化脚本（Windows 兼容）

用法：
    python scripts/init_db.py
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径 (在导入任何模块之前)
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from kv.core.config import Config
    from kv.core.database import Base
    from sqlalchemy import create_engine
except ImportError as e:
    print(f"ERROR: 缺少依赖包: {e}")
    print("\n请先安装依赖：")
    print("  pip install click sqlalchemy")
    sys.exit(1)


def init_database():
    """初始化数据库"""
    config = Config()

    # 确保数据目录存在
    config.data_dir.mkdir(parents=True, exist_ok=True)

    print(f"数据目录: {config.data_dir}")
    print(f"数据库文件: {config.db_path}")

    # 创建数据库引擎
    engine = create_engine(f"sqlite:///{config.db_path}")

    # 创建所有表
    Base.metadata.create_all(engine)

    print(f"✓ Database initialized at: {config.db_path}")
    print(f"✓ Created tables: items, collections, tags, item_tags, item_similarities")


if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
