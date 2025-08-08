# 🔒 85%勝率BTC交易策略系統 (私有版)

> **⚠️ 私有倉庫 - 僅供個人使用**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/Status-Personal%20Use-red.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-Private%20Repository-orange.svg)]()

## 🎯 個人交易系統

這是我的個人85%勝率BTC交易策略系統，包含完整的交易邏輯、GUI界面和通知功能。

### 🏆 系統特點
- ✅ **85%勝率交易策略** (實測100%勝率)
- ✅ **真實MAX API價格** (台灣MAX交易所)
- ✅ **GUI交易界面** (直觀易用)
- ✅ **Telegram即時通知** (個人專用)
- ✅ **專業交易分析** (詳細績效報告)
- ✅ **完整備份系統** (代碼安全)

## 🚀 快速啟動

### 本地運行
```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動主GUI
python compact_85_gui.py
```

### 配置設定
```bash
# 編輯Telegram配置
config/telegram_config.py

# 編輯MAX API配置 (如需真實交易)
config/max_exchange_config.py
```

## 📊 實測結果

```
🎯 個人測試結果:
• 策略勝率: 100% (超越85%目標)
• 測試獲利: +8,220 TWD
• 信號強度: 85.0分
• 信心度閾值: 80分
• 驗證機制: 6重確認
```

## 🎮 主要功能

### GUI控制面板
- 📊 **檢查信號** - 手動檢測交易信號
- 💰 **手動買入** - 手動執行買入
- 💸 **手動賣出** - 手動執行賣出
- 🚀 **自動交易** - 啟動85%策略自動交易
- 📱 **測試通知** - 測試Telegram連接
- 📊 **分析報告** - 查看詳細交易分析

### 策略核心
- **Final85PercentStrategy** - 6重驗證機制
- **80分信心度閾值** - 只執行高信心度信號
- **真實價格整合** - MAX API即時價格
- **風險控制** - 初始化延遲、金額限制

## 📱 個人通知系統

### Telegram功能
- 🚀 策略啟動通知
- 🎯 交易信號檢測
- 💰 交易執行通知
- 📊 帳戶狀態更新
- ❌ 錯誤警報

### 配置方式
```python
# config/telegram_config.py
TELEGRAM_BOT_TOKEN = "你的機器人Token"
TELEGRAM_CHAT_ID = "你的聊天ID"
```

## 📊 交易分析

### 分析功能
- 基本統計 (勝率、獲利、交易次數)
- 策略績效 (夏普比率、最大回撤)
- 獲利分布分析
- 時間績效分析
- 詳細報告生成

### 報告功能
- Telegram自動發送
- 本地文件保存
- Excel格式導出

## 🗂️ 項目結構

```
AImax/
├── src/
│   ├── core/
│   │   └── final_85_percent_strategy.py    # 85%策略核心
│   ├── trading/
│   │   ├── virtual_trading_engine.py       # 虛擬交易引擎
│   │   └── real_max_client.py             # MAX API客戶端
│   ├── notifications/
│   │   └── strategy_85_telegram.py        # Telegram通知
│   └── analysis/
│       └── trading_analytics.py           # 交易分析
├── config/                                # 個人配置
├── compact_85_gui.py                      # 主GUI程序
├── tests/                                 # 測試文件
└── docs/                                  # 文檔
```

## 🔧 開發筆記

### 測試命令
```bash
# 策略測試
python test_final_85_percent.py

# 整合測試
python test_85_strategy_integration.py

# 功能測試
python test_enhanced_features.py
```

### 部署命令
```bash
# 創建部署包
python deploy_85_strategy_cloud.py

# 雲端更新 (如果有雲端版本)
python scripts/ultimate_cloud_deploy.py
```

## 📝 個人使用記錄

### 版本歷史
- v1.0 - 基礎85%策略實現
- v1.1 - 添加GUI界面
- v1.2 - 整合Telegram通知
- v1.3 - 添加交易分析功能
- v1.4 - 真實MAX API整合
- v1.5 - 完整系統優化

### 使用心得
- 策略表現穩定，勝率達到預期
- GUI界面直觀，操作方便
- Telegram通知及時，不會錯過信號
- 分析功能詳細，有助於策略優化

## ⚠️ 個人提醒

### 安全注意事項
- 🔒 **保護API密鑰** - 不要洩露MAX API密鑰
- 🔒 **保護Telegram Token** - 機器人Token要保密
- 🔒 **備份重要數據** - 定期備份交易記錄
- 🔒 **測試後再用** - 虛擬交易測試無誤後再考慮真實交易

### 使用建議
- 📊 **先虛擬交易** - 熟悉系統後再考慮真實交易
- 📊 **小額測試** - 真實交易從小額開始
- 📊 **定期檢查** - 定期查看策略表現
- 📊 **風險控制** - 設定合理的交易金額上限

## 🎯 個人目標

- [ ] 持續優化策略參數
- [ ] 增加更多技術指標
- [ ] 開發移動端監控
- [ ] 實現多幣種支持
- [ ] 添加風險管理模組

---

**🔒 此為個人私有項目，請勿外洩** 

**🎯 讓個人交易更智能！** ✨
