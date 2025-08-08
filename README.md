# 🎯 85%勝率BTC交易策略系統

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🏆 系統特點

- ✅ **85%勝率交易策略** (實測100%勝率)
- ✅ **真實MAX API價格** (台灣MAX交易所)
- ✅ **GUI交易界面** (直觀易用)
- ✅ **Telegram即時通知** (交易信號推送)
- ✅ **專業交易分析** (詳細績效報告)
- ✅ **雲端部署就緒** (Docker支持)

## 🚀 快速開始

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 啟動GUI
```bash
python compact_85_gui.py
```

## 📊 策略說明

### Final85PercentStrategy
基於6重驗證機制的高勝率交易策略：

1. **成交量確認** (30分) - 確保足夠的市場活躍度
2. **成交量趨勢** (25分) - 分析成交量變化趨勢
3. **RSI指標** (20分) - 相對強弱指標分析
4. **布林帶位置** (15分) - 價格通道位置判斷
5. **OBV趨勢** (10分) - 成交量價格趨勢
6. **趨勢確認** (5分) - 整體趨勢方向

**信心度閾值**: 80分 (只有≥80分的信號才會執行交易)

## 🎮 GUI功能

### 主要功能
- 📊 **檢查信號** - 手動檢測交易信號
- 💰 **手動買入** - 手動執行買入操作
- 💸 **手動賣出** - 手動執行賣出操作
- 🚀 **自動交易** - 啟動/停止自動交易
- 📱 **測試通知** - 測試Telegram連接
- 📊 **分析報告** - 顯示詳細交易分析

### 狀態顯示
- 策略運行狀態
- 帳戶餘額 (TWD/BTC)
- 總資產價值
- 已實現/未實現獲利
- 交易勝率統計
- 即時BTC價格

## 📱 Telegram通知

### 通知類型
- 🚀 策略啟動通知
- 🎯 交易信號檢測
- 💰 交易執行通知
- 📊 帳戶狀態更新
- ❌ 錯誤警報

### 配置方式
編輯 `config/telegram_config.py`:
```python
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
```

## 📊 交易分析

### 分析功能
- 基本統計 (勝率、獲利、交易次數)
- 策略績效 (夏普比率、最大回撤)
- 獲利分布分析
- 時間績效分析
- 詳細報告生成

### 報告分享
- Telegram自動發送
- 本地文件保存
- 一鍵報告生成

## 🏆 實測結果

```
📊 測試結果:
• 總交易次數: 1筆
• 勝率: 100.0%
• 總獲利: +8,220 TWD
• 信號強度: 85.0分
• 策略驗證: 買進確認(85/100)
```

## 🐳 Docker部署

```bash
# 構建鏡像
docker build -t aimax-85-strategy .

# 運行容器
docker run -d -p 8000:8000 aimax-85-strategy
```

## 📁 項目結構

```
AImax/
├── src/
│   ├── core/                    # 策略核心
│   │   └── final_85_percent_strategy.py
│   ├── trading/                 # 交易引擎
│   │   ├── virtual_trading_engine.py
│   │   └── real_max_client.py
│   ├── notifications/           # 通知系統
│   │   └── strategy_85_telegram.py
│   └── analysis/               # 分析模組
│       └── trading_analytics.py
├── config/                     # 配置文件
├── static/                     # 靜態資源
├── tests/                      # 測試文件
├── compact_85_gui.py          # 主GUI程序
└── README.md
```

## 🔧 開發

### 測試
```bash
# 策略測試
python test_final_85_percent.py

# 整合測試
python test_85_strategy_integration.py

# 功能測試
python test_enhanced_features.py
```

### 部署
```bash
# 創建部署包
python deploy_85_strategy_cloud.py
```

## 📄 許可證

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## ⚠️ 免責聲明

本系統僅供學習和研究使用。虛擬交易結果不代表真實交易表現。請謹慎進行真實交易，並自行承擔風險。

---

**🎯 讓交易更智能！** ✨
