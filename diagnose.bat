@echo off
REM KnowIt 诊断工具

echo ========================================
echo KnowIt 模块诊断
echo ========================================
echo.

echo [1] 当前目录:
cd
echo.

echo [2] 目录结构:
if exist src (
    echo src 目录存在
    dir /b src
    echo.
    if exist src\kv (
        echo src\kv 目录存在
        dir /b src\kv
    ) else (
        echo src\kv 目录不存在！
    )
) else (
    echo src 目录不存在！
)
echo.

echo [3] Python 路径测试:
python scripts\diagnose.py

echo.
echo ========================================
echo.
echo 如果 import kv 失败，请使用以下命令：
echo.
echo   方法1: 使用 -m 模块运行
echo     python -m kv.cli --help
echo.
echo   方法2: 安装包到虚拟环境
echo     pip install -e .
echo.
echo ========================================
pause
