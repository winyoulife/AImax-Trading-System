@echo off
echo 🚀 上傳85%勝率策略系統到GitHub
echo.
echo 📋 請先在GitHub創建倉庫: aimax-85-strategy
echo 🔗 然後將下面的 YOUR_GITHUB_URL 替換為你的倉庫URL
echo.
echo 💻 執行以下命令:
echo.

REM 替換下面的URL為你的GitHub倉庫URL
set GITHUB_URL=https://github.com/YOUR_USERNAME/aimax-85-strategy.git

echo git remote add origin %GITHUB_URL%
echo git branch -M main  
echo git push -u origin main
echo.
echo 🎯 替換YOUR_USERNAME為你的GitHub用戶名後執行上述命令
pause

REM 如果你已經設置了正確的URL，取消下面三行的註釋並執行
REM git remote add origin %GITHUB_URL%
REM git branch -M main
REM git push -u origin main