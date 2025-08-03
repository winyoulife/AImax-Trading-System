# 項目最終清理計劃

## 🎯 清理目標
保留核心功能文件，刪除不必要的實驗性文件和重複文件，為後續開發做準備。

## ✅ 必須保留的核心文件

### 1. MACD核心文件 (最重要)
- `AImax/scripts/exact_macd_gui.py` - 完美的MACD GUI工具
- `AImax/scripts/compare_with_reference_data.py` - 參考數據比較工具
- `AImax/src/data/live_macd_service.py` - MACD數據服務
- `AImax/data/max_reference_macd_data.md` - 參考數據

### 2. 五大AI本地模組
- `AImax/src/ai/ai_manager.py` - 基礎AI管理器
- `AImax/src/ai/enhanced_ai_manager.py` - 增強AI管理器
- `AImax/src/ai/parallel_ai_manager.py` - 並行AI管理器
- `AImax/src/ai/ollama_client.py` - Ollama客戶端
- `setup_ollama_guide.md` - Ollama設置指南

### 3. 核心數據和API
- `AImax/src/data/max_client.py` - MAX API客戶端
- `AImax/src/data/technical_indicators.py` - 技術指標
- `AImax/src/data/historical_data_manager.py` - 歷史數據管理

### 4. 基礎配置
- `AImax/main.py` - 主程序入口
- `AImax/README.md` - 項目說明
- `config/` - 配置文件夾
- `AImax/CURRENT_STATUS.md` - 當前狀態

### 5. 重要規格文檔
- `.kiro/specs/ai-trading-system/` - AI交易系統規格
- `.kiro/specs/unified-trading-program/` - 統一交易程序規格

## ❌ 需要刪除的文件類別

### 1. 重複的MACD實驗文件
- 所有以 `macd_` 開頭的實驗性腳本 (除了保留的核心文件)
- 所有 `test_macd_` 開頭的測試文件
- 所有 `debug_macd_` 開頭的調試文件
- 所有 `reverse_engineer_` 開頭的逆向工程文件

### 2. 重複的GUI實驗文件
- 大部分 `test_gui_` 開頭的測試文件
- 重複的GUI實現文件
- 實驗性的圖表文件

### 3. 過時的規格文檔
- 已完成或廢棄的規格文件夾
- 重複的需求文檔

### 4. 測試和日誌文件
- `AImax/logs/` 文件夾中的舊日誌
- 大部分 `test_` 開頭的文件
- 臨時腳本文件

### 5. 文檔和報告文件
- 各種完成報告
- 開發日誌文件
- 清理計劃文件

## 🚀 清理後的項目結構

```
AImax/
├── main.py                           # 主程序
├── README.md                         # 項目說明
├── CURRENT_STATUS.md                 # 當前狀態
├── scripts/
│   ├── exact_macd_gui.py            # 核心MACD GUI
│   └── compare_with_reference_data.py # 參考數據比較
├── src/
│   ├── ai/                          # AI模組
│   │   ├── ai_manager.py
│   │   ├── enhanced_ai_manager.py
│   │   ├── parallel_ai_manager.py
│   │   └── ollama_client.py
│   ├── data/                        # 數據模組
│   │   ├── live_macd_service.py
│   │   ├── max_client.py
│   │   ├── technical_indicators.py
│   │   └── historical_data_manager.py
│   └── core/                        # 核心模組
└── data/
    └── max_reference_macd_data.md   # 參考數據

config/                              # 配置文件
.kiro/specs/                        # 重要規格文檔
setup_ollama_guide.md               # Ollama設置指南
```

## 📋 清理執行步驟

1. 備份核心文件
2. 刪除實驗性MACD文件
3. 刪除重複GUI文件
4. 刪除測試和日誌文件
5. 刪除過時文檔
6. 整理規格文檔
7. 驗證核心功能正常

## ⚠️ 注意事項

- 在刪除前確保核心文件功能正常
- 保留所有AI相關的核心模組
- 確保 `exact_macd_gui.py` 和 `compare_with_reference_data.py` 可以正常運行
- 保留必要的配置文件