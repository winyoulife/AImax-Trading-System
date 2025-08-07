# AImax 雲端更新標準作業程序 (SOP)

## 📋 概述
本文檔提供AImax交易系統雲端更新的標準化流程，避免更新錯誤和文件混淆問題。

## 🎯 更新工具

### 1. 自動化工具
- **主工具**: `scripts/cloud_update_manager.py`
- **快速執行**: `update_cloud.bat` (Windows)
- **配置文件**: `config/cloud_update_config.json`

### 2. 手動工具
- `scripts/force_cache_clear.py` - 強制清除緩存
- `scripts/fix_btc_price.py` - 修正BTC價格
- `scripts/check_github_actions.py` - 檢查部署狀態

## 🔄 標準更新流程

### 方法一：使用自動化工具 (推薦)

```bash
# 1. 雙擊執行
update_cloud.bat

# 或命令行執行
python scripts/cloud_update_manager.py
```

### 方法二：手動更新

```bash
# 1. 檢查當前狀態
python scripts/check_github_actions.py

# 2. 更新內容 (編輯 static/smart-balanced-dashboard.html)

# 3. 同步所有文件
copy static/smart-balanced-dashboard.html static/smart-balanced-dashboard-static.html

# 4. 提交更新
git add .
git commit -m "🔄 更新內容 - 描述"
git push origin main
```

## 📁 重要文件說明

### 主要文件
- **`static/smart-balanced-dashboard.html`** - 用戶實際訪問的主文件
- **`static/smart-balanced-dashboard-static.html`** - 備用文件

### 配置文件
- **`config/cloud_update_config.json`** - 更新配置
- **`.github/workflows/simple-deploy.yml`** - GitHub Actions部署配置

### 備份目錄
- **`backups/cloud_updates/`** - 自動備份目錄

## ⚠️ 常見錯誤避免

### 1. 文件名混淆
- ✅ 確保更新 `smart-balanced-dashboard.html` (用戶訪問的文件)
- ❌ 不要只更新 `smart-balanced-dashboard-static.html`

### 2. 版本標識
- ✅ 使用自動版本管理
- ❌ 不要手動修改版本號

### 3. 緩存問題
- ✅ 使用 `force_cache_clear.py` 創建多個版本
- ❌ 不要依賴瀏覽器自動更新

## 🔧 配置說明

### cloud_update_config.json
```json
{
  "main_dashboard_file": "smart-balanced-dashboard.html",  // 主文件
  "backup_enabled": true,                                  // 啟用備份
  "auto_version_increment": true,                         // 自動版本增加
  "target_files": [                                       // 同步目標文件
    "smart-balanced-dashboard.html",
    "smart-balanced-dashboard-static.html"
  ],
  "version_format": "v{major}.{minor}-{tag}",            // 版本格式
  "current_version": {                                    // 當前版本
    "major": 2,
    "minor": 2,
    "tag": "realtime"
  }
}
```

## 📊 更新檢查清單

### 更新前檢查
- [ ] 確認要更新的內容
- [ ] 檢查GitHub Actions狀態
- [ ] 確認主文件名稱正確

### 更新中檢查
- [ ] 備份已創建
- [ ] 版本號已更新
- [ ] 所有目標文件已同步
- [ ] Git提交成功

### 更新後檢查
- [ ] GitHub Actions部署成功
- [ ] 頁面版本標識正確
- [ ] 功能正常運作
- [ ] 緩存已清除

## 🚨 緊急處理

### 如果更新失敗
1. 檢查 `backups/cloud_updates/` 中的最新備份
2. 恢復備份文件
3. 重新執行更新流程

### 如果頁面不更新
1. 執行 `python scripts/force_cache_clear.py`
2. 訪問帶時間戳的新版本URL
3. 使用無痕模式或清除瀏覽器緩存

## 📞 支援資訊

### 相關文件
- `DEPLOYMENT_README.md` - 部署說明
- `GITHUB_SECRETS_SETUP.md` - GitHub配置
- `TROUBLESHOOTING.md` - 故障排除

### 常用命令
```bash
# 檢查狀態
python scripts/check_github_actions.py

# 強制更新
python scripts/force_cache_clear.py

# 修正BTC價格
python scripts/fix_btc_price.py

# 完整更新
python scripts/cloud_update_manager.py
```

## 📝 更新日誌

### v2.2-realtime (2025/08/08)
- 添加真實BTC價格API
- 修正緩存問題
- 創建標準化更新流程

### v2.1-stable (2025/08/07)
- 修正GitHub Actions部署問題
- 實現一買一賣交易邏輯
- 添加版本標識系統

---

**記住：使用自動化工具可以避免90%的更新錯誤！** 🚀