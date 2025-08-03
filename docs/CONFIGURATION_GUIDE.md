# ⚙️ AImax 多交易對交易系統配置指南

## 📋 **文檔概述**
**文檔版本**: 1.0  
**更新時間**: 2025年7月27日  
**適用版本**: AImax v1.0+  

## 🎯 **配置概述**

本指南詳細說明了AImax多交易對交易系統的各項配置選項，包括系統配置、AI模型配置、策略配置、風險管理配置等。正確的配置是系統穩定運行的基礎。

## 📁 **配置文件結構**

```
config/
├── trading_system.json      # 主系統配置
├── ai_models.json          # AI模型配置
AImax/config/
├── ai_models_qwen7b.json   # Qwen7B模型配置
└── (其他配置文件)
```

## 🔧 **主系統配置 (trading_system.json)**

### **基本配置**
```json
{
  "system": {
    "name": "AImax Multi-Pair Trading System",
    "version": "1.0.0",
    "environment": "production",
    "debug_mode": false,
    "log_level": "INFO"
  },
  "trading_pairs": [
    "BTCTWD", "ETHTWD", "LTCTWD", 
    "BCHTWD", "ADATWD", "DOTTWD"
  ],
  "data_sources": {
    "primary": "max_api",
    "backup": "local_cache",
    "update_interval": 1000,
    "retry_attempts": 3,
    "timeout_seconds": 30
  }
}
```

### **性能配置**
```json
{
  "performance": {
    "max_threads": 50,
    "memory_limit_mb": 2048,
    "api_rate_limit": 100,
    "cache_size_mb": 512,
    "gc_threshold": 0.8
  },
  "database": {
    "connection_pool_size": 20,
    "query_timeout": 30,
    "backup_interval_hours": 6,
    "cleanup_days": 30
  }
}
```

### **監控配置**
```json
{
  "monitoring": {
    "enabled": true,
    "metrics_interval": 60,
    "alert_thresholds": {
      "cpu_usage": 80,
      "memory_usage": 85,
      "disk_usage": 90,
      "response_time_ms": 1000
    },
    "notification": {
      "email_enabled": true,
      "webhook_enabled": true,
      "slack_enabled": false
    }
  }
}
```

## 🤖 **AI模型配置 (ai_models.json)**

### **市場掃描器配置**
```json
{
  "market_scanner": {
    "enabled": true,
    "model_name": "qwen2.5:7b",
    "scan_interval": 5,
    "sensitivity": 0.7,
    "pairs": "all",
    "indicators": ["volume", "price_change", "momentum"],
    "confidence_threshold": 0.6,
    "max_concurrent_scans": 6
  }
}
```

### **深度分析器配置**
```json
{
  "deep_analyzer": {
    "enabled": true,
    "model_name": "qwen2.5:7b",
    "analysis_depth": "high",
    "lookback_periods": 100,
    "confidence_threshold": 0.6,
    "technical_indicators": [
      "rsi", "macd", "bollinger_bands", 
      "moving_averages", "fibonacci"
    ],
    "analysis_timeout": 30
  }
}
```

### **趨勢分析器配置**
```json
{
  "trend_analyzer": {
    "enabled": true,
    "model_name": "qwen2.5:7b",
    "trend_periods": [5, 15, 30, 60],
    "trend_strength_threshold": 0.5,
    "pattern_recognition": true,
    "support_resistance": true,
    "fibonacci_levels": true
  }
}
```

### **風險評估器配置**
```json
{
  "risk_assessor": {
    "enabled": true,
    "model_name": "qwen2.5:7b",
    "risk_tolerance": "medium",
    "max_risk_per_trade": 0.02,
    "portfolio_risk_limit": 0.1,
    "volatility_threshold": 0.05,
    "correlation_analysis": true
  }
}
```

### **決策整合器配置**
```json
{
  "decision_integrator": {
    "enabled": true,
    "model_name": "qwen2.5:7b",
    "voting_method": "weighted",
    "min_consensus": 0.6,
    "weights": {
      "market_scanner": 0.2,
      "deep_analyzer": 0.25,
      "trend_analyzer": 0.25,
      "risk_assessor": 0.3
    },
    "decision_timeout": 10
  }
}
```

## 🎛️ **策略配置**

### **網格交易策略**
```json
{
  "grid_strategy": {
    "default_config": {
      "grid_levels": 10,
      "grid_spacing_percent": 2.0,
      "max_position_size": 0.1,
      "stop_loss_percent": 10.0,
      "take_profit_percent": 20.0,
      "rebalance_threshold": 0.05
    },
    "risk_limits": {
      "max_drawdown": 0.15,
      "max_open_orders": 20,
      "min_order_size": 0.001
    }
  }
}
```

### **DCA定投策略**
```json
{
  "dca_strategy": {
    "default_config": {
      "investment_amount": 1000,
      "frequency_hours": 24,
      "max_investment": 10000,
      "price_drop_threshold": 0.05,
      "ai_timing_enabled": true,
      "market_condition_filter": true
    },
    "risk_limits": {
      "max_position_size": 0.2,
      "stop_loss_percent": 20.0
    }
  }
}
```

### **AI信號策略**
```json
{
  "ai_signal_strategy": {
    "default_config": {
      "signal_source": "ai_analysis",
      "confidence_threshold": 0.7,
      "position_size_percent": 2.0,
      "max_positions": 5,
      "signal_timeout": 300,
      "follow_trend": true
    },
    "risk_limits": {
      "max_risk_per_signal": 0.03,
      "stop_loss_percent": 8.0
    }
  }
}
```

## 🛡️ **風險管理配置**

### **全局風險控制**
```json
{
  "global_risk": {
    "max_portfolio_risk": 0.1,
    "max_daily_loss": 0.05,
    "max_drawdown": 0.2,
    "position_size_limits": {
      "single_position": 0.1,
      "total_positions": 0.8,
      "per_pair": 0.2
    },
    "emergency_stop": {
      "enabled": true,
      "loss_threshold": 0.15,
      "volatility_threshold": 0.1
    }
  }
}
```

### **動態風險調整**
```json
{
  "dynamic_risk": {
    "enabled": true,
    "volatility_adjustment": true,
    "market_condition_adjustment": true,
    "performance_based_adjustment": true,
    "adjustment_factors": {
      "high_volatility": 0.5,
      "bear_market": 0.3,
      "poor_performance": 0.7
    }
  }
}
```

## 📊 **數據配置**

### **數據源配置**
```json
{
  "data_sources": {
    "max_api": {
      "enabled": true,
      "base_url": "https://max-api.maicoin.com",
      "rate_limit": 100,
      "timeout": 30,
      "retry_attempts": 3
    },
    "backup_sources": [
      {
        "name": "local_cache",
        "enabled": true,
        "cache_duration": 3600
      }
    ]
  }
}
```

### **數據處理配置**
```json
{
  "data_processing": {
    "cache_enabled": true,
    "cache_duration": 300,
    "data_validation": true,
    "outlier_detection": true,
    "smoothing_enabled": false,
    "compression_enabled": true
  }
}
```

## 🖥️ **GUI配置**

### **界面配置**
```json
{
  "gui": {
    "theme": "dark",
    "update_interval": 1000,
    "chart_settings": {
      "default_timeframe": "5m",
      "max_data_points": 500,
      "indicators_enabled": true
    },
    "notifications": {
      "sound_enabled": true,
      "popup_enabled": true,
      "system_tray": true
    }
  }
}
```

## 🔧 **部署配置**

### **生產環境配置**
```json
{
  "deployment": {
    "environment": "production",
    "auto_start": true,
    "restart_on_failure": true,
    "max_restart_attempts": 3,
    "health_check_interval": 60,
    "backup": {
      "enabled": true,
      "interval_hours": 6,
      "retention_days": 30
    }
  }
}
```

### **開發環境配置**
```json
{
  "deployment": {
    "environment": "development",
    "debug_mode": true,
    "hot_reload": true,
    "test_mode": true,
    "mock_trading": true,
    "log_level": "DEBUG"
  }
}
```

## 📝 **配置最佳實踐**

### **安全配置**
1. **API密鑰管理**
   - 使用環境變量存儲敏感信息
   - 定期輪換API密鑰
   - 限制API權限範圍

2. **訪問控制**
   - 設置強密碼
   - 啟用雙因素認證
   - 限制訪問IP範圍

### **性能優化**
1. **資源配置**
   - 根據硬件配置調整線程數
   - 合理設置內存限制
   - 優化數據庫連接池

2. **緩存策略**
   - 啟用適當的緩存
   - 設置合理的緩存時間
   - 監控緩存命中率

### **風險控制**
1. **保守配置**
   - 新用戶使用較低的風險參數
   - 逐步增加倉位大小
   - 設置嚴格的止損

2. **監控告警**
   - 設置合理的告警閾值
   - 啟用多種通知方式
   - 定期檢查系統狀態

## 🔄 **配置更新流程**

### **配置變更步驟**
1. **備份當前配置**
2. **修改配置文件**
3. **驗證配置格式**
4. **重啟相關服務**
5. **監控系統狀態**

### **配置驗證**
```bash
# 驗證配置文件格式
python -m aimax.config.validator

# 測試配置
python -m aimax.config.test_config

# 應用配置
python -m aimax.config.apply_config
```

## 🚨 **故障排除**

### **常見配置問題**
1. **JSON格式錯誤**: 檢查語法和逗號
2. **參數範圍錯誤**: 確認數值在有效範圍內
3. **權限問題**: 檢查文件讀寫權限
4. **依賴缺失**: 確認所需模塊已安裝

### **配置恢復**
```bash
# 恢復默認配置
python -m aimax.config.restore_defaults

# 從備份恢復
python -m aimax.config.restore_backup --date 2025-01-27
```

---

**📚 本配置指南提供了AImax系統的完整配置說明，確保系統正確運行。**

*文檔版本: 1.0*  
*更新時間: 2025年7月27日*  
*維護者: AImax開發團隊*