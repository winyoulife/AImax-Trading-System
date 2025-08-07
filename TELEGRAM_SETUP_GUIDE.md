# 📱 AImax Telegram通知系統設置指南

## 🎯 概述

AImax智能交易系統已集成完整的Telegram通知功能，支援：
- 🔥 高頻交易執行通知
- 📊 波動性變化警報
- 📈 每日性能摘要
- 🏥 系統健康監控
- 🚨 緊急停止警報
- 💰 價格閾值警報

## 🚀 快速設置步驟

### 步驟1: 創建Telegram機器人

1. 在Telegram中搜索 `@BotFather`
2. 發送 `/newbot` 命令
3. 按提示設置機器人名稱和用戶名
4. 獲得機器人Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 步驟2: 獲取Chat ID

1. 將你的機器人添加到群組或直接與機器人對話
2. 發送任意消息給機器人
3. 訪問：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. 在返回的JSON中找到 `"chat":{"id":123456789}` 中的數字

### 步驟3: 設置GitHub Secrets

1. 進入你的GitHub倉庫
2. 點擊 `Settings` → `Secrets and variables` → `Actions`
3. 點擊 `New repository secret`
4. 添加以下兩個Secrets：

```
名稱: TELEGRAM_BOT_TOKEN
值: 你的機器人Token

名稱: TELEGRAM_CHAT_ID  
值: 你的Chat ID
```

## 🧪 測試通知系統

設置完成後，你可以通過以下方式測試：

### 方法1: GitHub Actions手動觸發

1. 進入 `Actions` 頁面
2. 選擇 `AImax Telegram通知系統`
3. 點擊 `Run workflow`
4. 選擇 `test_message` 類型
5. 點擊 `Run workflow`

### 方法2: 本地測試腳本

```bash
# 設置環境變量
export TELEGRAM_BOT_TOKEN="你的機器人Token"
export TELEGRAM_CHAT_ID="你的Chat ID"

# 運行測試
python src/notifications/high_frequency_telegram_service.py
```

## 📋 通知類型說明

### 🔥 高頻交易執行通知
- **觸發條件**: 每次交易策略執行
- **頻率控制**: 最多每分鐘1次
- **內容**: 執行狀態、BTC價格、波動性、信心度

### 📊 波動性變化警報  
- **觸發條件**: 市場波動性等級變化
- **頻率控制**: 最多每3分鐘1次
- **內容**: 波動性變化、價格變化、頻率調整

### 📈 每日性能摘要
- **觸發條件**: 每日自動發送
- **頻率控制**: 每24小時1次
- **內容**: 執行統計、勝率、盈虧、性能評級

### 🏥 系統健康監控
- **觸發條件**: 系統異常檢測
- **頻率控制**: 最多每10分鐘1次
- **內容**: 系統狀態、問題列表、建議操作

### 🚨 緊急停止警報
- **觸發條件**: 緊急停止觸發
- **頻率控制**: 無限制（重要警報）
- **內容**: 停止原因、影響範圍、處理建議

### 💰 價格閾值警報
- **觸發條件**: BTC價格突破設定閾值
- **頻率控制**: 最多每5分鐘1次
- **內容**: 當前價格、閾值、系統響應

## ⚙️ 高級配置

### 自定義通知頻率

編輯 `src/notifications/high_frequency_telegram_service.py` 中的 `notification_cooldowns`：

```python
self.notification_cooldowns = {
    'price_alert': 300,      # 價格警報：5分鐘
    'volatility_change': 180, # 波動性變化：3分鐘
    'execution_result': 60,   # 執行結果：1分鐘
    'system_error': 600,     # 系統錯誤：10分鐘
    'daily_summary': 86400,  # 每日摘要：24小時
}
```

### 自定義消息格式

你可以修改各個通知方法中的消息模板來自定義格式。

## 🔧 故障排除

### 常見問題

**1. 機器人無法發送消息**
- 檢查Bot Token是否正確
- 確認機器人沒有被封禁
- 驗證Chat ID是否正確

**2. GitHub Actions執行失敗**
- 檢查Secrets是否正確設置
- 查看Actions日誌中的錯誤信息
- 確認網路連接正常

**3. 收不到通知**
- 檢查機器人是否被靜音
- 確認你在正確的聊天中
- 驗證通知頻率限制

### 調試命令

```bash
# 測試機器人連接
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"

# 測試發送消息
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>" \
     -d "text=測試消息"

# 獲取聊天更新
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

## 📊 通知統計

系統會自動記錄通知歷史：
- `data/notifications/telegram_history_YYYY-MM-DD.jsonl` - 每日通知記錄
- `data/notifications/latest_notification.json` - 最新通知狀態

## 🔒 安全建議

1. **保護Bot Token**: 絕不要在代碼中硬編碼Token
2. **限制機器人權限**: 只給機器人必要的權限
3. **定期更新Token**: 如有安全疑慮，及時重新生成Token
4. **監控使用情況**: 定期檢查機器人的使用日誌

## 📞 支援

如果遇到問題：
1. 檢查GitHub Actions日誌
2. 查看 `data/notifications/` 目錄下的記錄
3. 參考Telegram Bot API文檔
4. 檢查系統監控面板：https://winyoulife.github.io/AImax-Trading-System/

---

🎉 **恭喜！你的AImax智能交易系統現在具備完整的Telegram通知功能！**

💡 **提示**: 建議先發送測試消息確認一切正常，然後享受83.3%勝率策略帶來的智能通知體驗！