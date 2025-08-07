# AImax 一鍵部署指南

## 🚀 快速開始

AImax智能交易系統提供多種部署方式，選擇最適合您的方式：

### 方式1: Python完整部署腳本 (推薦)

**適用於**: 所有平台，功能最完整

```bash
python3 deploy_aimax.py
```

**特色**:
- ✅ 完整的互動式配置嚮導
- ✅ 自動環境檢查和依賴驗證
- ✅ 詳細的部署報告和日誌
- ✅ 自動生成配置指南
- ✅ 支援多種部署模式

### 方式2: Linux/macOS 快速腳本

**適用於**: Linux和macOS系統

```bash
chmod +x quick_deploy.sh
./quick_deploy.sh
```

**特色**:
- ⚡ 快速部署，5分鐘完成
- 🎨 彩色輸出，用戶友好
- 🔧 自動配置文件修改
- 📋 自動生成設置指南

### 方式3: Windows 批處理腳本

**適用於**: Windows系統

```cmd
quick_deploy.bat
```

**特色**:
- 🪟 Windows原生支持
- 🔒 隱藏密碼輸入
- 📁 自動項目結構創建
- 📋 完整的設置指南

## 📋 部署前準備

### 必需軟件
- **Git**: 版本控制
- **Python 3.8+**: 運行部署腳本
- **GitHub帳號**: 託管代碼和網站

### 可選配置
- **MAX交易所帳號**: 如需真實交易
- **Telegram Bot**: 如需通知功能

## 🔧 部署流程

### 1. 選擇部署方式
根據您的操作系統選擇合適的部署腳本

### 2. 運行部署腳本
按照提示輸入配置信息：
- GitHub用戶名
- 倉庫名稱
- 登入帳號密碼
- 功能選項

### 3. 完成GitHub設置
- 創建GitHub倉庫
- 推送代碼
- 設置GitHub Pages
- 配置Secrets (可選)

### 4. 訪問您的網站
等待2-3分鐘部署完成後，訪問您的專屬交易系統

## 📊 部署後配置

### GitHub Secrets配置

訪問: `https://github.com/您的用戶名/倉庫名/settings/secrets/actions`

**基礎配置**:
- `ADMIN_USERNAME`: 您的登入帳號
- `ADMIN_PASSWORD_HASH`: 自動生成的密碼哈希

**交易配置** (可選):
- `MAX_API_KEY`: MAX交易所API密鑰
- `MAX_API_SECRET`: MAX交易所API密鑰密碼

**Telegram通知** (可選):
- `TELEGRAM_BOT_TOKEN`: Telegram Bot Token
- `TELEGRAM_CHAT_ID`: Telegram Chat ID

## 🎯 功能特色

### 🔐 安全認證
- SHA-256密碼加密
- 24小時會話管理
- 專屬帳號系統

### 💰 交易功能
- 83.3%勝率MACD策略
- MAX API即時價格
- 智能頻率控制
- GitHub Actions自動執行

### 📊 監控面板
- 即時系統狀態
- GitHub Actions監控
- 交易執行統計
- 響應式設計

### ⚡ 性能優化
- HTML/CSS/JS壓縮
- 靜態資源優化
- CDN加速
- 緩存控制

## 🆘 故障排除

### 常見問題

**Q: Python版本不符合要求**
A: 請安裝Python 3.8或更高版本

**Q: Git命令不存在**
A: 請安裝Git並確保添加到PATH

**Q: 無法連接GitHub**
A: 檢查網路連接和防火牆設置

**Q: 部署後無法訪問網站**
A: 等待2-3分鐘讓GitHub Actions完成部署

**Q: 登入失敗**
A: 檢查帳號密碼是否正確，清除瀏覽器緩存

### 獲取幫助

1. 查看部署日誌和報告
2. 檢查GitHub Actions運行狀態
3. 查看項目文檔
4. 提交GitHub Issue

## 📈 升級指南

### 更新系統
1. 備份當前配置
2. 下載最新版本
3. 重新運行部署腳本
4. 恢復個人配置

### 版本歷史
- **v3.0**: 完整的一鍵部署系統
- **v2.0**: GitHub Actions集成
- **v1.0**: 基礎交易系統

## 🤝 貢獻

歡迎提交Issue和Pull Request來改進AImax系統！

## 📄 許可證

本項目採用MIT許可證，詳見LICENSE文件。

---

🤖 **AImax智能交易系統** - 讓交易變得更智能！