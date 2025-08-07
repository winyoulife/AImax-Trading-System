@echo off
echo ========================================
echo AImax 快速更新工具
echo ========================================
echo.

cd /d "%~dp0"

echo 🔄 執行快速更新...
python scripts/quick_update.py --all

echo.
echo ✅ 更新完成！
echo 🌐 請等待2-3分鐘後刷新頁面查看更新
echo 📋 如果頁面沒有更新，請按 Ctrl+F5 強制刷新
echo.
pause