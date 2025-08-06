#!/bin/bash

# AImax 快速部署腳本 (Linux/macOS)
# 一鍵部署AImax智能交易系統

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印帶顏色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    echo "=================================================================="
    print_message $CYAN "🤖 AImax 智能交易系統 - 快速部署工具 v3.0"
    echo "=================================================================="
    echo ""
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message $RED "❌ $1 未安裝，請先安裝 $1"
        exit 1
    else
        print_message $GREEN "✅ $1 已安裝"
    fi
}

# 檢查前置條件
check_prerequisites() {
    print_message $BLUE "🔍 檢查部署前置條件..."
    
    check_command "git"
    check_command "python3"
    
    # 檢查Python版本
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 1 ]]; then
        print_message $GREEN "✅ Python版本: $python_version"
    else
        print_message $RED "❌ Python版本需要3.8或更高，當前版本: $python_version"
        exit 1
    fi
    
    # 檢查網路連接
    if ping -c 1 github.com &> /dev/null; then
        print_message $GREEN "✅ 網路連接正常"
    else
        print_message $RED "❌ 無法連接到GitHub"
        exit 1
    fi
}

# 獲取用戶配置
get_user_config() {
    print_message $BLUE "⚙️  配置部署參數..."
    
    echo ""
    read -p "請輸入您的GitHub用戶名: " GITHUB_USERNAME
    
    if [[ -z "$GITHUB_USERNAME" ]]; then
        print_message $RED "❌ GitHub用戶名不能為空"
        exit 1
    fi
    
    DEFAULT_REPO="${GITHUB_USERNAME}-AImax-Trading"
    read -p "請輸入倉庫名稱 (預設: $DEFAULT_REPO): " REPO_NAME
    REPO_NAME=${REPO_NAME:-$DEFAULT_REPO}
    
    read -p "請輸入登入帳號 (預設: admin): " LOGIN_USERNAME
    LOGIN_USERNAME=${LOGIN_USERNAME:-admin}
    
    echo ""
    read -s -p "請輸入登入密碼: " LOGIN_PASSWORD
    echo ""
    read -s -p "請確認密碼: " CONFIRM_PASSWORD
    echo ""
    
    if [[ "$LOGIN_PASSWORD" != "$CONFIRM_PASSWORD" ]]; then
        print_message $RED "❌ 密碼不匹配"
        exit 1
    fi
    
    if [[ ${#LOGIN_PASSWORD} -lt 6 ]]; then
        print_message $RED "❌ 密碼長度至少6位"
        exit 1
    fi
    
    # 生成密碼哈希
    LOGIN_PASSWORD_HASH=$(echo -n "$LOGIN_PASSWORD" | sha256sum | cut -d' ' -f1)
    
    print_message $GREEN "✅ 配置完成"
}

# 創建項目
create_project() {
    print_message $BLUE "📁 創建項目結構..."
    
    if [[ -d "$REPO_NAME" ]]; then
        print_message $YELLOW "⚠️  目錄 $REPO_NAME 已存在"
        read -p "是否覆蓋? (y/N): " OVERWRITE
        if [[ "$OVERWRITE" =~ ^[Yy]$ ]]; then
            rm -rf "$REPO_NAME"
            print_message $GREEN "🗑️  已刪除現有目錄"
        else
            print_message $RED "❌ 用戶取消部署"
            exit 1
        fi
    fi
    
    # 複製項目文件
    cp -r . "$REPO_NAME"
    cd "$REPO_NAME"
    
    # 清理不需要的文件
    rm -rf .git __pycache__ *.pyc .env 2>/dev/null || true
    
    print_message $GREEN "✅ 項目結構創建完成"
}

# 自定義配置
customize_config() {
    print_message $BLUE "⚙️  自定義配置文件..."
    
    # 更新登入配置
    if [[ -f "static/secure-login-fixed.html" ]]; then
        sed -i.bak "s/lovejk1314/$LOGIN_USERNAME/g" static/secure-login-fixed.html
        sed -i.bak "s/898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae/$LOGIN_PASSWORD_HASH/g" static/secure-login-fixed.html
        rm static/secure-login-fixed.html.bak 2>/dev/null || true
        print_message $GREEN "✅ 更新登入頁面配置"
    fi
    
    if [[ -f "web_app.py" ]]; then
        sed -i.bak "s/lovejk1314/$LOGIN_USERNAME/g" web_app.py
        sed -i.bak "s/898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae/$LOGIN_PASSWORD_HASH/g" web_app.py
        rm web_app.py.bak 2>/dev/null || true
        print_message $GREEN "✅ 更新Web應用配置"
    fi
    
    # 創建部署配置
    cat > aimax_config.json << EOF
{
  "project_name": "$REPO_NAME",
  "github_username": "$GITHUB_USERNAME",
  "login_username": "$LOGIN_USERNAME",
  "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "3.0",
  "deployment_method": "quick_deploy_script"
}
EOF
    
    print_message $GREEN "✅ 配置文件自定義完成"
}

# 初始化Git
init_git() {
    print_message $BLUE "📦 初始化Git倉庫..."
    
    git init
    git add .
    git commit -m "🚀 初始化 AImax 智能交易系統 v3.0 - $(date '+%Y-%m-%d %H:%M:%S')"
    
    print_message $GREEN "✅ Git倉庫初始化完成"
}

# 創建部署指南
create_guides() {
    print_message $BLUE "📋 創建部署指南..."
    
    # 創建GitHub設置指南
    cat > GITHUB_SETUP_GUIDE.md << EOF
# GitHub 設置指南

## 1. 創建GitHub倉庫
1. 訪問: https://github.com/new
2. 倉庫名稱: $REPO_NAME
3. 設為私有倉庫 (推薦)
4. 不要初始化README、.gitignore或LICENSE
5. 創建倉庫

## 2. 推送代碼
\`\`\`bash
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
git branch -M main
git push -u origin main
\`\`\`

## 3. 設置GitHub Pages
1. 訪問: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: / (root)
5. 點擊Save

## 4. 配置Secrets (可選)
訪問: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions

必需的Secrets:
- \`ADMIN_USERNAME\`: $LOGIN_USERNAME
- \`ADMIN_PASSWORD_HASH\`: $LOGIN_PASSWORD_HASH

## 5. 訪問網站
網站地址: https://$GITHUB_USERNAME.github.io/$REPO_NAME/
登入帳號: $LOGIN_USERNAME
EOF

    # 創建快速開始指南
    cat > QUICK_START.md << EOF
# AImax 快速開始指南

## 🎉 恭喜！您的AImax智能交易系統已準備就緒

### 📋 部署信息
- 項目名稱: $REPO_NAME
- GitHub用戶: $GITHUB_USERNAME
- 登入帳號: $LOGIN_USERNAME
- 部署時間: $(date '+%Y-%m-%d %H:%M:%S')

### 🚀 下一步操作
1. 按照 GITHUB_SETUP_GUIDE.md 完成GitHub設置
2. 等待GitHub Actions完成部署 (約2-3分鐘)
3. 訪問您的網站: https://$GITHUB_USERNAME.github.io/$REPO_NAME/
4. 使用您設置的帳號密碼登入

### 🔧 功能特色
- 🔐 專屬帳號密碼認證
- 💰 MAX API 即時BTC價格
- 🤖 85%勝率交易策略
- 📊 GitHub Actions 狀態監控
- 📱 響應式設計
- ⚡ 優化的性能

### 📞 支持
如有問題，請查看項目文檔或提交Issue。
EOF

    print_message $GREEN "✅ 部署指南創建完成"
}

# 主函數
main() {
    print_header
    
    check_prerequisites
    get_user_config
    create_project
    customize_config
    init_git
    create_guides
    
    echo ""
    echo "=================================================================="
    print_message $GREEN "🎉 AImax 快速部署完成！"
    echo "=================================================================="
    echo ""
    print_message $CYAN "📁 項目目錄: $(pwd)"
    print_message $CYAN "🌐 預期網站地址: https://$GITHUB_USERNAME.github.io/$REPO_NAME/"
    print_message $CYAN "🔐 登入帳號: $LOGIN_USERNAME"
    print_message $CYAN "📋 設置指南: GITHUB_SETUP_GUIDE.md"
    print_message $CYAN "🚀 快速開始: QUICK_START.md"
    echo ""
    print_message $YELLOW "⏳ 下一步: 按照 GITHUB_SETUP_GUIDE.md 完成GitHub設置"
    echo ""
}

# 執行主函數
main