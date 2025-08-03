# AImax - 智能MACD交易系統

## 📈 系統概述

AImax是一個基於1小時MACD策略的智能交易監控系統，結合回測分析和即時監控功能，提供專業級的交易信號檢測和Telegram通知服務。

## 🎯 核心功能

### 💰 交易策略表現
- **總獲利**: 108,774 TWD
- **勝率**: 62.5% (5勝3敗)
- **平均每筆獲利**: 13,597 TWD
- **交易頻率**: 約每週1-2次信號

### 🔧 主要特色
- **1小時MACD策略** - 基於金叉/死叉的成熟策略
- **即時監控** - 每小時自動檢測新的交易信號
- **Telegram通知** - 即時推送詳細的交易分析
- **詳細信號分析** - 包含信號強度、風險評估、操作建議
- **回測功能** - 完整的歷史數據回測和統計分析

## 🚀 快速開始

### 環境要求
- Python 3.8+
- 所需套件見 `requirements.txt`

### 安裝步驟
1. 克隆倉庫
```bash
git clone <repository-url>
cd AImax
```

2. 創建虛擬環境
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. 安裝依賴
```bash
pip install -r requirements.txt
```

### 使用方式

#### 1. 即時監控系統（推薦）
```bash
python scripts/live_macd_monitor_gui.py
```
- 自動啟用Telegram通知
- 每小時檢測新信號
- 詳細技術分析

#### 2. 乾淨版回測分析
```bash
python scripts/clean_macd_backtest_gui.py
```
- 專注於1小時MACD策略
- 歷史回測數據分析

#### 3. 策略比較分析
```bash
python scripts/compare_macd_vs_ma.py
```
- MACD vs MA策略比較
- 詳細獲利分析

## 📊 信號分析系統

### 信號強度分級
- 🔥 **強信號** - MACD柱狀圖 > 50
- ⚡ **中信號** - MACD柱狀圖 20-50  
- 💫 **弱信號** - MACD柱狀圖 < 20

### 風險評估
- 🟢 **低風險** - 深度超賣/超買區域
- 🟡 **中風險** - 一般超賣/超買
- 🔴 **高風險** - 高位買進/低位賣出

### 操作建議
- 💎 **優質信號，建議執行**
- ⚖️ **謹慎觀察，適量操作**
- ⚠️ **高風險信號，建議觀望**

## 📱 Telegram通知

系統支援自動Telegram通知，包含：
- 即時交易信號推送
- 詳細技術分析報告
- 系統狀態更新
- 回測總結報告

## 📁 項目結構

```
AImax/
├── src/                          # 核心源碼
│   ├── core/                     # 核心交易邏輯
│   │   ├── improved_trading_signals.py    # 1小時MACD策略
│   │   └── multi_timeframe_trading_signals.py  # 多時框策略
│   ├── data/                     # 數據服務
│   │   └── live_macd_service.py  # 即時數據獲取
│   └── notifications/            # 通知服務
│       └── telegram_service.py   # Telegram通知
├── scripts/                      # 執行腳本
│   ├── live_macd_monitor_gui.py  # 即時監控系統
│   ├── clean_macd_backtest_gui.py # 乾淨版回測
│   ├── compare_macd_vs_ma.py     # 策略比較
│   └── test_*.py                 # 測試腳本
├── data/                         # 數據存儲
├── config/                       # 配置文件
└── requirements.txt              # 依賴套件
```

## 🔬 測試

運行測試腳本驗證系統功能：

```bash
# 測試Telegram通知
python scripts/test_my_telegram.py

# 測試即時監控
python scripts/test_live_telegram.py

# 測試乾淨版MACD
python scripts/test_clean_macd.py
```

## 📈 歷史表現

基於500筆1小時歷史數據的回測結果：

| 指標 | 數值 |
|------|------|
| 總獲利 | 108,774 TWD |
| 完整交易對 | 8對 |
| 勝率 | 62.5% |
| 平均獲利 | 13,597 TWD |
| 平均持倉時間 | 23.6小時 |

## ⚠️ 風險聲明

本系統僅供學習和研究使用，不構成投資建議。交易有風險，投資需謹慎。

## 📄 授權

本項目採用MIT授權條款。

## 🤝 貢獻

歡迎提交Issue和Pull Request來改進系統。

---

**AImax - 讓交易更智能** 🚀