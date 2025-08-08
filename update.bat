@echo off
chcp 65001 >nul
title AImax 雲端更新工具

echo.
echo ========================================
echo 🚀 AImax 雲端更新工具
echo ========================================
echo.
echo 📋 這是唯一正確的更新方法！
echo ⚠️  請不要使用其他舊的更新腳本
echo.

:: 檢查是否在正確的目錄
if not exist "scripts\ultimate_cloud_deploy.py" (
    echo ❌ 錯誤：請在 AImax 項目根目錄執行此腳本
    echo 📁 當前目錄：%cd%
    echo.
    pause
    exit /b 1
)

:: 執行終極雲端部署
echo 🚀 正在執行終極雲端部署...
echo.
python scripts\ultimate_cloud_deploy.py

:: 檢查執行結果
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 🎉 雲端更新成功完成！
    echo ========================================
    echo.
    echo 📖 詳細說明請查看: CLOUD_UPDATE_GUIDE.md
    echo 🌐 請使用工具提供的URL訪問更新後的頁面
) else (
    echo.
    echo ========================================
    echo ❌ 雲端更新失敗！
    echo ========================================
    echo.
    echo 📖 故障排除請查看: CLOUD_UPDATE_GUIDE.md
    echo 🔧 請檢查網絡連接和Git狀態
)

echo.
pause