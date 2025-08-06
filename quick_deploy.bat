@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: AImax 快速部署腳本 (Windows)
:: 一鍵部署AImax智能交易系統

title AImax 智能交易系統 - 快速部署工具 v3.0

echo.
echo ==================================================================
echo 🤖 AImax 智能交易系統 - 快速部署工具 v3.0
echo ==================================================================
echo.

:: 檢查前置條件
echo 🔍 檢查部署前置條件...

:: 檢查Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git未安裝，請先安裝Git
    pause
    exit /b 1
) else (
    echo ✅ Git已安裝
)

:: 檢查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安裝，請先安裝Python 3.8+
    pause
    exit /b 1
) else (
    echo ✅ Python已安裝
)

:: 檢查網路連接
ping -n 1 github.com >nul 2>&1
if errorlevel 1 (
    echo ❌ 無法連接到GitHub
    pause
    exit /b 1
) else (
    echo ✅ 網路連接正常
)

echo.
echo ⚙️ 配置部署參數...

:: 獲取GitHub用戶名
set /p GITHUB_USERNAME="請輸入您的GitHub用戶名: "
if "!GITHUB_USERNAME!"=="" (
    echo ❌ GitHub用戶名不能為空
    pause
    exit /b 1
)

:: 獲取倉庫名稱
set DEFAULT_REPO=!GITHUB_USERNAME!-AImax-Trading
set /p REPO_NAME="請輸入倉庫名稱 (預設: !DEFAULT_REPO!): "
if "!REPO_NAME!"=="" set REPO_NAME=!DEFAULT_REPO!

:: 獲取登入帳號
set /p LOGIN_USERNAME="請輸入登入帳號 (預設: admin): "
if "!LOGIN_USERNAME!"=="" set LOGIN_USERNAME=admin

:: 獲取密碼
echo.
echo 請輸入登入密碼 (輸入時不會顯示):
call :GetPassword LOGIN_PASSWORD
echo.
echo 請確認密碼:
call :GetPassword CONFIRM_PASSWORD

if not "!LOGIN_PASSWORD!"=="!CONFIRM_PASSWORD!" (
    echo ❌ 密碼不匹配
    pause
    exit /b 1
)

:: 檢查密碼長度
call :StrLen LOGIN_PASSWORD PASSWORD_LENGTH
if !PASSWORD_LENGTH! LSS 6 (
    echo ❌ 密碼長度至少6位
    pause
    exit /b 1
)

:: 生成密碼哈希 (使用Python)
for /f "delims=" %%i in ('python -c "import hashlib; print(hashlib.sha256('''!LOGIN_PASSWORD!'''.encode()).hexdigest())"') do set LOGIN_PASSWORD_HASH=%%i

echo ✅ 配置完成

echo.
echo 📁 創建項目結構...

:: 檢查目錄是否存在
if exist "!REPO_NAME!" (
    echo ⚠️ 目錄 !REPO_NAME! 已存在
    set /p OVERWRITE="是否覆蓋? (y/N): "
    if /i "!OVERWRITE!"=="y" (
        rmdir /s /q "!REPO_NAME!"
        echo 🗑️ 已刪除現有目錄
    ) else (
        echo ❌ 用戶取消部署
        pause
        exit /b 1
    )
)

:: 複製項目文件
xcopy /e /i /q . "!REPO_NAME!" >nul
cd "!REPO_NAME!"

:: 清理不需要的文件
if exist .git rmdir /s /q .git >nul 2>&1
if exist __pycache__ rmdir /s /q __pycache__ >nul 2>&1
del *.pyc >nul 2>&1
del .env >nul 2>&1

echo ✅ 項目結構創建完成

echo.
echo ⚙️ 自定義配置文件...

:: 更新登入配置文件
if exist "static\secure-login-fixed.html" (
    powershell -Command "(Get-Content 'static\secure-login-fixed.html') -replace 'lovejk1314', '!LOGIN_USERNAME!' | Set-Content 'static\secure-login-fixed.html'"
    powershell -Command "(Get-Content 'static\secure-login-fixed.html') -replace '898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae', '!LOGIN_PASSWORD_HASH!' | Set-Content 'static\secure-login-fixed.html'"
    echo ✅ 更新登入頁面配置
)

if exist "web_app.py" (
    powershell -Command "(Get-Content 'web_app.py') -replace 'lovejk1314', '!LOGIN_USERNAME!' | Set-Content 'web_app.py'"
    powershell -Command "(Get-Content 'web_app.py') -replace '898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae', '!LOGIN_PASSWORD_HASH!' | Set-Content 'web_app.py'"
    echo ✅ 更新Web應用配置
)

:: 創建部署配置文件
(
echo {
echo   "project_name": "!REPO_NAME!",
echo   "github_username": "!GITHUB_USERNAME!",
echo   "login_username": "!LOGIN_USERNAME!",
echo   "deployed_at": "!date! !time!",
echo   "version": "3.0",
echo   "deployment_method": "quick_deploy_batch"
echo }
) > aimax_config.json

echo ✅ 配置文件自定義完成

echo.
echo 📦 初始化Git倉庫...

git init >nul
git add . >nul
git commit -m "🚀 初始化 AImax 智能交易系統 v3.0 - !date! !time!" >nul

echo ✅ Git倉庫初始化完成

echo.
echo 📋 創建部署指南...

:: 創建GitHub設置指南
(
echo # GitHub 設置指南
echo.
echo ## 1. 創建GitHub倉庫
echo 1. 訪問: https://github.com/new
echo 2. 倉庫名稱: !REPO_NAME!
echo 3. 設為私有倉庫 ^(推薦^)
echo 4. 不要初始化README、.gitignore或LICENSE
echo 5. 創建倉庫
echo.
echo ## 2. 推送代碼
echo ```bash
echo git remote add origin https://github.com/!GITHUB_USERNAME!/!REPO_NAME!.git
echo git branch -M main
echo git push -u origin main
echo ```
echo.
echo ## 3. 設置GitHub Pages
echo 1. 訪問: https://github.com/!GITHUB_USERNAME!/!REPO_NAME!/settings/pages
echo 2. Source: Deploy from a branch
echo 3. Branch: main
echo 4. Folder: / ^(root^)
echo 5. 點擊Save
echo.
echo ## 4. 配置Secrets ^(可選^)
echo 訪問: https://github.com/!GITHUB_USERNAME!/!REPO_NAME!/settings/secrets/actions
echo.
echo 必需的Secrets:
echo - `ADMIN_USERNAME`: !LOGIN_USERNAME!
echo - `ADMIN_PASSWORD_HASH`: !LOGIN_PASSWORD_HASH!
echo.
echo ## 5. 訪問網站
echo 網站地址: https://!GITHUB_USERNAME!.github.io/!REPO_NAME!/
echo 登入帳號: !LOGIN_USERNAME!
) > GITHUB_SETUP_GUIDE.md

:: 創建快速開始指南
(
echo # AImax 快速開始指南
echo.
echo ## 🎉 恭喜！您的AImax智能交易系統已準備就緒
echo.
echo ### 📋 部署信息
echo - 項目名稱: !REPO_NAME!
echo - GitHub用戶: !GITHUB_USERNAME!
echo - 登入帳號: !LOGIN_USERNAME!
echo - 部署時間: !date! !time!
echo.
echo ### 🚀 下一步操作
echo 1. 按照 GITHUB_SETUP_GUIDE.md 完成GitHub設置
echo 2. 等待GitHub Actions完成部署 ^(約2-3分鐘^)
echo 3. 訪問您的網站: https://!GITHUB_USERNAME!.github.io/!REPO_NAME!/
echo 4. 使用您設置的帳號密碼登入
echo.
echo ### 🔧 功能特色
echo - 🔐 專屬帳號密碼認證
echo - 💰 MAX API 即時BTC價格
echo - 🤖 85%勝率交易策略
echo - 📊 GitHub Actions 狀態監控
echo - 📱 響應式設計
echo - ⚡ 優化的性能
echo.
echo ### 📞 支持
echo 如有問題，請查看項目文檔或提交Issue。
) > QUICK_START.md

echo ✅ 部署指南創建完成

echo.
echo ==================================================================
echo 🎉 AImax 快速部署完成！
echo ==================================================================
echo.
echo 📁 項目目錄: %cd%
echo 🌐 預期網站地址: https://!GITHUB_USERNAME!.github.io/!REPO_NAME!/
echo 🔐 登入帳號: !LOGIN_USERNAME!
echo 📋 設置指南: GITHUB_SETUP_GUIDE.md
echo 🚀 快速開始: QUICK_START.md
echo.
echo ⏳ 下一步: 按照 GITHUB_SETUP_GUIDE.md 完成GitHub設置
echo.

pause
exit /b 0

:: 獲取密碼函數 (隱藏輸入)
:GetPassword
set "psCommand=powershell -Command "$pword = read-host -AsSecureString; $BSTR=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword); [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)""
for /f "usebackq delims=" %%p in (`%psCommand%`) do set "%~1=%%p"
goto :eof

:: 計算字符串長度函數
:StrLen
setlocal enabledelayedexpansion
set "str=!%~1!"
set "len=0"
for /l %%i in (0,1,8191) do (
    if "!str:~%%i,1!"=="" (
        set /a len=%%i
        goto :StrLen_end
    )
)
:StrLen_end
endlocal & set "%~2=%len%"
goto :eof