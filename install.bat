@echo off
REM KnowIt 包安装脚本（Windows）

echo ========================================
echo KnowIt 包安装到虚拟环境
echo ========================================
echo.

REM 检查是否在项目根目录
if not exist "pyproject.toml" (
    echo ERROR: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo 正在安装 kv 包...
echo 这将安装 kv 包到当前 Python 环境
echo.

pip install -e .

if errorlevel 1 (
    echo.
    echo ========================================
    echo 安装失败！
    echo.
    echo 可能的原因：
    echo 1. pip 不在 PATH 中
    echo 2. Python 版本过低（需要 3.10+）
    echo 3. 权限问题
    echo.
    echo 请检查上述问题后重试
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装成功！
echo.
echo 测试命令：
echo   python -m kv.cli --help
echo   或
echo   kv --help
echo ========================================
echo.
pause
