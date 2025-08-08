@echo off
chcp 65001 >nul
title AImax 真實交易系統

echo.
echo ========================================
echo 🎯 AImax 真實交易系統
echo ========================================
echo 📊 基於台灣MAX交易所的真實交易系統
echo 💰 為10萬台幣實戰準備
echo.

:: 檢查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，請先安裝Python
    pause
    exit /b 1
)

:: 檢查必要文件
if not exist "real_trading_gui.py" (
    echo ❌ 找不到GUI文件
    pause
    exit /b 1
)

if not exist "real_trading_server.py" (
    echo ❌ 找不到服務器文件
    pause
    exit /b 1
)

:: 啟動選擇器
python start_real_trading.py

pause