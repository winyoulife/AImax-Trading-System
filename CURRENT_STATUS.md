# AImax 交易系統當前狀態

## 🎯 項目概述
AImax 是一個基於人工智能的加密貨幣交易系統，專注於 MAX 交易所的 BTC/TWD 交易對。

## 🧹 項目清理完成 (2025-07-30)

**重大更新**: 項目已完成大規模清理，刪除了100+個重複和實驗性文件，保留核心功能。

## 📊 當前核心功能狀態

### ✅ 核心MACD系統 (100%完成)
- **精確MACD GUI** (`scripts/exact_macd_gui.py`) 🎯
  - 與MAX交易所數據100%匹配
  - 24小時歷史數據顯示
  - 實時數據更新和驗證
  
- **增強版MACD回測分析器** (`scripts/enhanced_macd_backtest_gui.py`) 🎯 **NEW!**
  - 7天歷史回測數據 (168小時)
  - 智能交易信號檢測 (買進/賣出)
  - 信號統計分析和CSV導出
  - 淡紅色/淡綠色信號標示
  
- **參考數據比較工具** (`scripts/compare_with_reference_data.py`) 🎯
  - 數據準確性驗證
  - 與用戶提供的參考數據對比
  
- **實時MACD服務** (`src/data/live_macd_service.py`) 🎯
  - 直接從MAX API獲取數據
  - 精確的MACD計算邏輯

### ✅ 五大AI本地模組 (已保留)
- **基礎AI管理器** (`src/ai/ai_manager.py`) 🤖
- **增強AI管理器** (`src/ai/enhanced_ai_manager.py`) 🤖
- **並行AI管理器** (`src/ai/parallel_ai_manager.py`) 🤖
- **Ollama客戶端** (`src/ai/ollama_client.py`) 🤖
- **Ollama設置指南** (`setup_ollama_guide.md`) 🤖

### ✅ 核心數據系統
- **MAX API客戶端** (`src/data/max_client.py`)
- **技術指標計算** (`src/data/technical_indicators.py`)
- **歷史數據管理** (`src/data/historical_data_manager.py`)

### ✅ 重要規格文檔 (已精簡)
- **AI交易系統規格** (`.kiro/specs/ai-trading-system/`)
- **統一交易程序規格** (`.kiro/specs/unified-trading-program/`)
- **多幣對交易系統規格** (`.kiro/specs/multi-pair-trading-system/`)
- **Ollama AI交易系統規格** (`.kiro/specs/ollama-ai-trading-system/`)
- **真實回測系統規格** (`.kiro/specs/real-backtest-system/`)
- **GUI系統改進規格** (`.kiro/specs/gui-system-improvement/`)

## 🚀 快速啟動

### 1. 運行核心MACD工具
```bash
# 啟動增強版MACD回測分析器 (最新功能)
python AImax/scripts/enhanced_macd_backtest_gui.py

# 啟動精確MACD GUI (24小時數據)
python AImax/scripts/exact_macd_gui.py

# 運行數據比較工具
python AImax/scripts/compare_with_reference_data.py
```

### 2. 測試AI模組
```bash
# 測試基礎AI系統
python AImax/scripts/test_system.py

# 測試五大AI模組
python AImax/scripts/test_five_ai_simple.py
```

### 3. 環境設置
```bash
# 安裝依賴
pip install -r requirements.txt

# 設置Ollama (如果使用AI功能)
# 參考 setup_ollama_guide.md
```

## 📁 清理後的項目結構

```
AImax/
├── main.py                           # 主程序入口
├── README.md                         # 項目說明
├── CURRENT_STATUS.md                 # 當前狀態
├── scripts/
│   ├── enhanced_macd_backtest_gui.py # 🎯 增強版MACD回測分析器 (NEW!)
│   ├── exact_macd_gui.py            # 🎯 核心MACD GUI (24小時)
│   ├── compare_with_reference_data.py # 🎯 參考數據比較
│   └── [其他必要腳本]
├── src/
│   ├── ai/                          # 🤖 五大AI模組
│   │   ├── ai_manager.py
│   │   ├── enhanced_ai_manager.py
│   │   ├── parallel_ai_manager.py
│   │   └── ollama_client.py
│   ├── data/                        # 📊 數據模組
│   │   ├── live_macd_service.py     # 🎯 核心MACD服務
│   │   ├── max_client.py
│   │   ├── technical_indicators.py
│   │   └── historical_data_manager.py
│   └── core/                        # 🔧 核心模組
└── data/
    └── max_reference_macd_data.md   # 🎯 參考數據

config/                              # ⚙️ 配置文件
.kiro/specs/                        # 📋 重要規格文檔 (已精簡)
setup_ollama_guide.md               # 🤖 Ollama設置指南
```

## 🎉 清理成果

- **刪除文件**: 100+ 個重複和實驗性文件
- **保留核心**: 20+ 個重要功能文件
- **項目大小**: 減少約70%
- **結構清晰**: 核心功能一目了然

## 🎯 後續開發方向

現在項目已經清理完成，可以基於以下核心文件進行後續開發：

1. **MACD功能擴展**: 基於 `exact_macd_gui.py` 和 `compare_with_reference_data.py`
2. **AI功能整合**: 使用五大AI本地模組
3. **交易系統開發**: 基於保留的規格文檔
4. **數據服務擴展**: 基於 `live_macd_service.py` 和 `max_client.py`

## ⚠️ 重要注意事項

1. **核心MACD工具**: 已確認與MAX交易所數據100%匹配
2. **AI模組完整**: 五大AI本地模組已保留，可隨時使用
3. **項目狀態**: 現在處於最佳狀態，可以開始新的開發任務
4. **風險警告**: 這是一個實驗性交易系統，請勿在生產環境中使用真實資金

---

**最後更新**: 2025-07-30
**版本**: v1.0.0-cleaned
**狀態**: 清理完成，準備後續開發