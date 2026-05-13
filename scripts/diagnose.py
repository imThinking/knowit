"""
KnowIt 模块导入测试

用于诊断 Python 路径问题
"""

import sys
from pathlib import Path

print("=" * 60)
print("KnowIt 模块诊断工具")
print("=" * 60)

# 1. 当前工作目录
print("\n[1] 当前工作目录:")
print(f"  {Path.cwd()}")

# 2. Python 路径
print("\n[2] Python 路径:")
src_path = Path.cwd() / "src"
if src_path.exists():
    print(f"  ✓ src 目录存在: {src_path}")
    if str(src_path) not in sys.path:
        print(f"  ! src 目录不在 sys.path 中")
        print(f"  正在添加...")
        sys.path.insert(0, str(src_path))
        print(f"  ✓ 已添加: {src_path}")
    else:
        print(f"  ✓ src 目录已在 sys.path 中")
else:
    print(f"  ✗ src 目录不存在: {src_path}")

# 3. 测试导入
print("\n[3] 测试模块导入:")
try:
    import kv
    print(f"  ✓ import kv 成功")
    print(f"  模块位置: {kv.__file__}")
except ImportError as e:
    print(f"  ✗ import kv 失败: {e}")

try:
    from kv.core.config import Config
    print(f"  ✓ from kv.core.config import Config 成功")
except ImportError as e:
    print(f"  ✗ from kv.core.config import Config 失败: {e}")

try:
    from kv.cli import cli
    print(f"  ✓ from kv.cli import cli 成功")
except ImportError as e:
    print(f"  ✗ from kv.cli import cli 失败: {e}")

# 4. 列出 kv 目录内容
print("\n[4] kv 目录内容:")
kv_path = Path.cwd() / "src" / "kv"
if kv_path.exists():
    for item in kv_path.iterdir():
        print(f"  - {item.name}/" if item.is_dir() else f"  - {item.name}")
else:
    print(f"  ✗ kv 目录不存在: {kv_path}")

# 5. 建议
print("\n[5] 解决方案:")
print("  如果看到 import kv 失败，尝试：")
print("  方法1: python -m kv.cli --help")
print("  方法2: export PYTHONPATH=src:$PYTHONPATH (Linux)")
print("  方法3: pip install -e . (安装包到虚拟环境)")

print("\n" + "=" * 60)
