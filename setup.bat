@echo off
REM KnowIt 项目初始化脚本 (Windows PowerShell)

echo ========================================
echo KnowIt 项目初始化
echo ========================================
echo.

REM 1. 检查 Python 版本
echo [1/5] 检查 Python 版本...
python --version
if errorlevel 1 (
    echo ERROR: Python 未安装或不在 PATH 中
    echo 请访问 https://www.python.org/downloads/ 安装 Python 3.10+
    pause
    exit /b 1
)
echo OK: Python 已安装
echo.

REM 2. 检查项目目录
echo [2/5] 检查项目目录...
if not exist "pyproject.toml" (
    echo ERROR: 请在项目根目录运行此脚本
    pause
    exit /b 1
)
echo OK: 在项目根目录
echo.

REM 3. 安装依赖
echo [3/5] 安装 Python 依赖...
echo 正在安装依赖包...
pip install click sqlalchemy beautifulsoup4 lxml simhash
if errorlevel 1 (
    echo WARNING: 部分包安装失败，尝试继续...
)
echo OK: 核心依赖已安装
echo.

REM 4. 创建虚拟环境（可选但推荐）
echo [4/5] 创建虚拟环境...
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)
echo OK: 虚拟环境已创建
echo.

REM 5. 初始化数据库
echo [5/5] 初始化数据库...
python scripts\init_db.py
if errorlevel 1 (
    echo ERROR: 数据库初始化失败
    pause
    exit /b 1
)
echo.
echo ========================================
echo KnowIt 项目初始化完成！
echo ========================================
echo.
echo 下一步：
echo   1. 激活虚拟环境: venv\Scripts\Activate.ps1
echo   2. 测试 CLI: python -m kv.cli --help
echo   3. 添加内容: python -m kv.cli add https://example.com
echo.
pause
