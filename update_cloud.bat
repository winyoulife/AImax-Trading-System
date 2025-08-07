@echo off
echo ========================================
echo AImax 雲端更新工具
echo ========================================
echo.

cd /d "%~dp0"

echo 🔄 啟動雲端更新管理器...
python scripts/cloud_update_manager.py

echo.
echo ✅ 更新完成！
echo 🌐 請等待2-3分鐘後刷新頁面查看更新
echo.
pause