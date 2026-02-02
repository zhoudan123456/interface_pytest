@echo off
REM 设置UTF-8编码以支持中文输出
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo 招标文件检查点验证工具（UTF-8版）
echo ========================================
echo.

REM 执行Python脚本
python run_llm_matcher.py %*

echo.
pause
