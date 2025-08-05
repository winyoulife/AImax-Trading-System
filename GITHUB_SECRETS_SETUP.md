# GitHub Secrets 設置指南

## 🔒 為AImax私有交易系統設置GitHub Secrets

為了確保你的交易系統完全私有和安全，需要在GitHub倉庫中設置以下Secrets：

### 1. 進入GitHub倉庫設置

1. 打開你的GitHub倉庫頁面
2. 點擊 "Settings" 標籤
3. 在左側菜單中點擊 "Secrets and variables" > "Actions"

### 2. 添加必要的Secrets

點擊 "New repository secret" 按鈕，添加以下Secrets：

#### GITHUB_TOKEN
- **名稱**: `GITHUB_TOKEN`
- **值**: 你的GitHub Personal Access Token
- **用途**: 用於API訪問和工作流程控制

**如何獲取GitHub Token:**
1. 進入 GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
2. 點擊 "Generate new token (classic)"
3. 選擇權限: `repo`, `workflow`, `read:user`
4. 複製生成的token並保存到此Secret

#### AUTH_HASH
- **名稱**: `AUTH_HASH`
- **值**: 你的登入密碼的SHA-256雜湊值
- **用途**: 用於網頁登入認證

**如何生成AUTH_HASH:**
```bash
# 使用你的密碼替換 "your_password"
echo -n "your_password" | sha256sum
```

或者使用線上工具生成SHA-256雜湊值。

#### REPO_OWNER
- **名稱**: `REPO_OWNER`
- **值**: 你的GitHub用戶名
- **用途**: 用於API請求

#### REPO_NAME
- **名稱**: `REPO_NAME`
- **值**: `AImax`
- **用途**: 倉庫名稱

### 3. 啟用GitHub Pages

1. 在倉庫設置中找到 "Pages" 選項
2. 在 "Source" 中選擇 "GitHub Actions"
3. 確保倉庫設置為 "Private"

### 4. 驗證設置

設置完成後，推送代碼到倉庫，GitHub Actions會自動：
1. 構建你的私有網頁
2. 注入環境變數
3. 部署到GitHub Pages
4. 只有你能訪問

### 5. 安全提醒

⚠️ **重要安全事項:**
- 絕對不要在代碼中硬編碼任何敏感資訊
- 定期更新你的GitHub Token
- 確保倉庫始終保持私有狀態
- 不要與他人分享你的Secrets值

### 6. 訪問你的私有監控面板

設置完成後，你可以通過以下網址訪問：
- `https://your-username.github.io/AImax/`

只有你能夠訪問這個網址，因為倉庫是私有的。

## 🔧 故障排除

如果遇到問題：
1. 檢查所有Secrets是否正確設置
2. 確認GitHub Token權限足夠
3. 查看GitHub Actions執行日誌
4. 確保倉庫為私有狀態