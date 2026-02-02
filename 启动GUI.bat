@echo off
REM 投标文件检查工具启动脚本
REM 自动设置环境变量并启动GUI

echo 正在设置环境变量...
set ZHIPUAI_API_KEY=cd3b673bfa3041b489b92f9188c314e4.9UAWLn2qUTdIjS8C

echo 环境变量已设置
echo 正在启动GUI...
echo.

python bid_check_gui.py

pause
