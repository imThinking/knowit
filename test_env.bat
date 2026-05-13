@echo off
REM KnowIt 开发环境快速测试脚本

echo ========================================
echo KnowIt 环境测试
echo ========================================
echo.

python scripts\test_setup.py

echo.
echo ========================================
echo 如果测试通过，尝试运行 CLI：
echo   python -m kv.cli --help
echo ========================================
echo.
pause
