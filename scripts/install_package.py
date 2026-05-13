"""
KnowIt 包安装脚本

将 kv 包安装到虚拟环境
"""

import sys
from pathlib import Path

print("=" * 60)
print("KnowIt 包安装")
print("=" * 60)

# 获取项目根目录
project_root = Path(__file__).parent
print(f"\n项目根目录: {project_root}")

# 检查 pyproject.toml
if (project_root / "pyproject.toml").exists():
    print("✓ pyproject.toml 存在")
else:
    print("✗ pyproject.toml 不存在")
    sys.exit(1)

# 安装包
print("\n正在安装 kv 包到虚拟环境...")
print("运行: pip install -e .")
print()

import subprocess
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", "."],
    cwd=project_root
)

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("✓ 安装成功！")
    print("\n测试命令：")
    print("  python -m kv.cli --help")
    print("  或直接：")
    print("  kv --help")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("✗ 安装失败")
    print("=" * 60)
    sys.exit(result.returncode)
