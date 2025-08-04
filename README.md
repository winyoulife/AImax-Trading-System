# AImax - 智能MACD交易系統

## 📈 系統概述

AImax是一個基於MACD策略的智能交易監控系統，結合多種技術指標分析，提供專業級的交易信號檢測。

## 🎯 核心功能

### 💰 交易策略表現
- **智能平衡策略**: 85.7%勝率
- **進階策略**: 75.0%勝率  
- **基礎策略**: 66.7%勝率

### 🔧 主要特色
- **多重策略** - 從基礎到智能平衡的多層策略
- **技術指標分析** - MACD、RSI、布林帶、成交量分析
- **風險控制** - 多重驗證和風險管理機制
- **Telegram通知** - 即時推送交易信號

## 🚀 快速開始

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 運行策略測試
```bash
# 測試智能平衡策略
python scripts/test_smart_balanced_volume_macd.py

# 測試進階策略
python scripts/test_advanced_volume_macd.py

# 測試基礎策略
python scripts/test_volume_enhanced_macd.py
```

### 啟動GUI界面
```bash
python scripts/volume_enhanced_macd_gui.py
```

## 📊 策略比較

| 策略版本 | 勝率 | 交易次數 | 特色 |
|---------|------|----------|------|
| 智能平衡版本 | 85.7% | 7筆 | 動態閾值調整 |
| 進階版本 | 75.0% | 8筆 | 多重指標驗證 |
| 基礎版本 | 66.7% | 3筆 | 簡單MACD策略 |

## 🛡️ 安全功能

- **模擬交易模式** - 零風險測試
- **緊急停止機制** - 多重安全控制
- **風險管理** - 每日限制和停損設定

## 🔧 系統架構

```
AImax/
├── src/core/           # 核心交易策略
├── src/data/           # 數據獲取
├── src/notifications/  # 通知系統
├── scripts/           # 測試和GUI腳本
└── config/            # 配置文件
```

## ⚠️ 免責聲明

本系統僅供學習和研究使用。加密貨幣交易存在風險，請謹慎投資。