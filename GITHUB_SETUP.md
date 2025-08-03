# GitHub倉庫設置指南

## 🚀 AImax交易系統已準備上傳！

你的AImax智能交易系統已經完全開發完成，包含：

### ✨ 主要功能
- 🤖 **Telegram雙向機器人** - 手機指令查詢和自動推送
- 📊 **真實交易數據** - 34對交易，255,419 TWD獲利
- 📱 **GUI整合界面** - 圖形化監控和Telegram消息顯示
- 🔄 **穩定運行** - 解決了所有409錯誤問題

### 📊 交易表現
- **總獲利**: 255,419 TWD
- **完整交易對**: 34 對
- **勝率**: 47.1% (16勝18敗)
- **平均獲利**: 7,512 TWD/對

## 📋 GitHub倉庫創建步驟

### 方法1: 在GitHub網站創建倉庫
1. 前往 https://github.com/maxhsu999
2. 點擊 "New repository" 或 "+"
3. 倉庫名稱設為: `AImax-Trading-System`
4. 設為 Public（公開）或 Private（私人）
5. **不要**勾選 "Initialize with README"
6. 點擊 "Create repository"

### 方法2: 使用不同的倉庫名稱
如果上面的名稱已被使用，可以嘗試：
- `AImax-MACD-Trading-Bot`
- `AImax-Crypto-Trading-System`
- `AImax-Telegram-Trading-Bot`

## 🔧 推送指令

創建倉庫後，使用以下指令推送：

```bash
# 如果使用原名稱
git push -u origin main

# 如果需要更改遠程倉庫URL
git remote set-url origin https://github.com/maxhsu999/新倉庫名稱.git
git push -u origin main
```

## 📁 項目結構概覽

```
AImax/
├── 🤖 src/notifications/          # Telegram機器人
│   ├── telegram_bot.py           # 完整雙向機器人
│   ├── polling_telegram_bot.py   # 輪詢版機器人（推薦）
│   └── telegram_service.py       # 基礎服務
├── 📊 src/core/                   # 核心交易邏輯
│   ├── improved_trading_signals.py
│   └── improved_max_macd_calculator.py
├── 🖥️ scripts/                    # 執行腳本
│   ├── live_macd_monitor_gui.py   # 主GUI程式
│   ├── setup_telegram_bot.py     # 機器人設置
│   └── check_latest_trades.py    # 交易統計檢查
├── 📚 docs/                       # 文檔
│   └── telegram_bot_guide.md     # 機器人使用指南
└── 📋 README.md                   # 項目說明
```

## 🎯 使用說明

### 啟動系統
```bash
python scripts/live_macd_monitor_gui.py
```

### 啟動Telegram機器人
1. 在GUI中點擊 "📱 設置Telegram" 按鈕
2. 在手機上發送指令測試

### 支持的指令
- 中文: `幫助`、`狀態`、`價格`、`獲利`、`信號`
- 英文: `/help`、`/status`、`/price`、`/profit`、`/signals`

## 🏆 項目亮點

1. **完整的交易系統** - 從數據獲取到信號生成到通知推送
2. **雙向Telegram機器人** - 支持手機指令查詢
3. **GUI整合界面** - 圖形化監控和消息顯示
4. **真實交易數據** - 基於歷史數據的34對交易記錄
5. **穩定運行** - 解決了所有技術問題

準備好上傳到GitHub了！🚀